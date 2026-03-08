# Chapter 8 — Data Pipeline

## Build Roadmap Position
- Stage: Execution Flow
- You are here: Chapter 8
- Before this: Chapter 7
- After this: Chapter 9

## Learning Objectives
- Understand how data enters, transforms, persists, and exits this system.
- Identify write pipelines, read/report pipelines, and initialization pipelines.
- Map where validation, scoping, audit logging, and export formatting occur.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 8 — Data Pipeline

## Learning Goals
- Understand how data enters, transforms, persists, and exits this system.
- Identify write pipelines, read/report pipelines, and initialization pipelines.
- Map where validation, scoping, audit logging, and export formatting occur.

## Reference Files
- `inventory/views.py`
- `inventory/serializers.py`
- `actions/views.py`
- `audit/utils.py`
- `reports/views.py`
- `common/access.py`
- `common/management/commands/seed_prd_data.py`
- `catalog/management/commands/seed_initial_categories.py`

## Pipeline Categories in This Project
1. Transactional API write pipelines (create/update/bulk import)
2. Transactional stock mutation pipeline
3. Assignment pipeline
4. Audit trail pipeline
5. Read aggregation/report/export pipeline
6. Bootstrap/seed data pipeline

## 1) Inventory Item Create/Update Pipeline
```text
HTTP request
-> inventory viewset action
-> serializer validation (category/item_type rules)
-> model save
-> audit log write (CREATE/UPDATE + snapshot)
-> response payload
```

Observed implementation:
- Input source: JSON body to `InventoryItemViewSet`.
- Validation: `InventoryItemSerializer.validate`.
- Persistence: `serializer.save()`.
- Side effect: `create_inventory_audit_log(...)` with `item_snapshot(...)`.

## 2) Inventory Bulk Import Pipeline (`/inventory-items/bulk-import/`)
```text
CSV file upload
-> decode + DictReader rows
-> row-to-payload mapping
-> per-row serializer validation
-> save valid rows
-> per-row audit log
-> aggregate result {created, failed, errors}
```

Observed behavior:
- Row errors are accumulated; processing continues for other rows.
- Pipeline output is summary JSON instead of single-record response.

## 3) Consumable Stock Transaction Pipeline
```text
HTTP POST stock transaction
-> serializer validate_quantity
-> atomic create()
   -> read stock
   -> compute new balance by transaction type
   -> reject if insufficient quantity
   -> update stock.quantity
   -> create transaction with balance_after
-> view perform_create
   -> set performed_by
   -> create audit log
   -> optional low-stock email alert
-> response
```

Observed controls:
- Transactional integrity: `@transaction.atomic` in serializer `create`.
- Business rule: stock cannot go negative for `STOCK_OUT`/`DAMAGE`.
- External notification: email on threshold breach when recipients are configured.

## 4) Assignment Pipeline
```text
assignment request (single or bulk)
-> serializer validation (target user/office required, return rules)
-> save assignment
-> audit log write (ASSIGN or RETURN)
-> response or bulk summary
```

Observed in `actions/views.py`:
- Both single-create/update and CSV bulk-import produce audit records.
- Summary pipeline also exists (`summary-by-assignee`) as grouped output.

## 5) Audit Pipeline (Cross-Cutting)
```text
business event in inventory/actions
-> create_inventory_audit_log(...)
-> InventoryAuditLog row
-> later consumed by audit endpoints and report endpoints
```

Audit data is a downstream data source for:
- audit log API (`audit` app)
- recent activity report (`reports` app)

## 6) Read/Report/Export Pipeline
### Dashboard and report JSON
```text
request
-> scoped queryset per user office access
-> ORM filters/aggregations/annotations
-> structured JSON response
```

### Export pipelines
- CSV export: iterate queryset and write lines to `HttpResponse(text/csv)`.
- Excel export: build workbook (`openpyxl`) and stream `.xlsx` response.
- PDF export: draw report rows via `reportlab` canvas and stream `.pdf` response.

## 7) Initialization / Seed Pipeline
From management commands:
```text
seed_prd_data command
-> call seed_initial_categories
-> seed offices
-> seed users
-> seed custom fields
-> seed inventory (+ subtype records)
-> seed assignments
-> seed stock transactions
-> seed audit logs
```

Observed characteristics:
- Idempotent update-or-create style across multiple steps.
- Dry-run mode wraps in transaction and rolls back.
- Category seeding pipeline is separated into dedicated command.

## Common Pipeline Guards
- Permission guard: `IMSAccessPermission`
- Data visibility guard: `scope_queryset_by_user`
- Serializer guards: domain validation and quantity checks
- Database guards: model constraints and transaction blocks

## Pipeline Outputs
- Operational outputs:
  - resource JSON from CRUD endpoints
  - summary JSON from bulk/report endpoints
- Artifact outputs:
  - CSV/Excel/PDF report downloads
- Side-effect outputs:
  - audit rows
  - optional low-stock email notifications

## What Is Missing
- No asynchronous queue-based data pipeline is wired in visible app code.
- No stream/event processor module is present.

## Chapter 8 Outcome
You now have a full data pipeline view from ingest (JSON/CSV/commands) through validation, scoped persistence, audit/notification side effects, and final outputs (JSON and exported files).
```

## Topic 2 — Actual Implementation (Exact Repo Code)
### File: `inventory/views.py`
```python
import csv
import io

from django.conf import settings
from django.core.mail import send_mail
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.models import InventoryActionType
from audit.utils import create_inventory_audit_log, item_snapshot
from common.access import scope_queryset_by_user
from common.permissions import IMSAccessPermission
from .models import ConsumableStock, ConsumableStockTransaction, FixedAsset, InventoryItem
from .serializers import (
    ConsumableStockSerializer,
    ConsumableStockTransactionSerializer,
    FixedAssetSerializer,
    InventoryItemSerializer,
)


class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.select_related("category", "office").all().order_by("id")
    serializer_class = InventoryItemSerializer
    filterset_fields = ["category", "office", "status", "item_type"]
    search_fields = ["title", "item_number", "category__name", "office__name"]
    ordering_fields = ["id", "title", "item_number", "created_at", "updated_at"]
    ordering = ["-created_at"]
    permission_classes = [IMSAccessPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        return scope_queryset_by_user(queryset, self.request.user, "office_id")

    def perform_create(self, serializer):
        item = serializer.save()
        create_inventory_audit_log(
            item=item,
            action_type=InventoryActionType.CREATE,
            user=self.request.user,
            after_data=item_snapshot(item),
            remarks="Inventory item created",
        )

    def perform_update(self, serializer):
        before = item_snapshot(self.get_object())
        item = serializer.save()
        create_inventory_audit_log(
            item=item,
            action_type=InventoryActionType.UPDATE,
            user=self.request.user,
            before_data=before,
            after_data=item_snapshot(item),
            remarks="Inventory item updated",
        )

    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

        decoded = file_obj.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))
        created_count = 0
        errors = []

        for index, row in enumerate(reader, start=2):
            payload = {
                "title": row.get("title"),
                "item_number": row.get("item_number") or None,
                "item_type": row.get("item_type"),
                "status": row.get("status"),
                "category": row.get("category"),
                "office": row.get("office"),
                "amount": row.get("amount") or 0,
                "price": row.get("price") or 0,
                "currency": row.get("currency") or "",
                "store": row.get("store") or "",
                "project": row.get("project") or "",
                "department": row.get("department") or "",
                "manufacturer": row.get("manufacturer") or "",
                "description": row.get("description") or "",
            }
            serializer = self.get_serializer(data=payload)
            if serializer.is_valid():
                item = serializer.save()
                create_inventory_audit_log(
                    item=item,
                    action_type=InventoryActionType.CREATE,
                    user=request.user,
                    after_data=item_snapshot(item),
                    remarks="Inventory item created (bulk import)",
                )
                created_count += 1
            else:
                errors.append({"line": index, "errors": serializer.errors})

        return Response(
            {"created": created_count, "failed": len(errors), "errors": errors},
            status=status.HTTP_200_OK,
        )


class FixedAssetViewSet(viewsets.ModelViewSet):
    queryset = FixedAsset.objects.select_related("item").all().order_by("id")
    serializer_class = FixedAssetSerializer
    filterset_fields = ["item"]
    search_fields = ["asset_tag", "serial_number", "item__title"]
    ordering_fields = ["id", "purchase_date", "warranty_expiry_date"]
    ordering = ["id"]
    permission_classes = [IMSAccessPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        return scope_queryset_by_user(queryset, self.request.user, "item__office_id")


class ConsumableStockViewSet(viewsets.ModelViewSet):
    queryset = ConsumableStock.objects.select_related("item").all().order_by("id")
    serializer_class = ConsumableStockSerializer
    filterset_fields = ["item", "reorder_alert_enabled"]
    search_fields = ["item__title", "unit"]
    ordering_fields = ["id", "quantity", "min_threshold"]
    ordering = ["id"]
    permission_classes = [IMSAccessPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        return scope_queryset_by_user(queryset, self.request.user, "item__office_id")


class ConsumableStockTransactionViewSet(viewsets.ModelViewSet):
    queryset = ConsumableStockTransaction.objects.select_related(
        "stock",
        "stock__item",
        "performed_by",
        "assigned_to",
    ).all().order_by("id")
    serializer_class = ConsumableStockTransactionSerializer
    filterset_fields = ["stock", "transaction_type", "status", "performed_by", "assigned_to"]
    search_fields = ["stock__item__title", "stock__item__item_number", "description", "department"]
    ordering_fields = ["id", "created_at", "quantity", "balance_after"]
    ordering = ["-created_at"]
    permission_classes = [IMSAccessPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        return scope_queryset_by_user(queryset, self.request.user, "stock__item__office_id")

    def perform_create(self, serializer):
        transaction_obj = serializer.save(performed_by=self.request.user)
        item = transaction_obj.stock.item
        action_type = InventoryActionType.UPDATE
        if transaction_obj.transaction_type == "STOCK_OUT":
            action_type = InventoryActionType.RETURN
        create_inventory_audit_log(
            item=item,
            action_type=action_type,
            user=self.request.user,
            after_data={
                "transaction_type": transaction_obj.transaction_type,
                "quantity": str(transaction_obj.quantity),
                "balance_after": str(transaction_obj.balance_after),
                "stock_id": transaction_obj.stock_id,
            },
            remarks="Consumable stock transaction",
        )

        stock = transaction_obj.stock
        if stock.reorder_alert_enabled and stock.quantity <= stock.min_threshold:
            recipients = [email for email in getattr(settings, "LOW_STOCK_ALERT_EMAILS", []) if email]
            if recipients:
                send_mail(
                    subject=f"Low stock alert: {stock.item.title}",
                    message=(
                        f"Item: {stock.item.title}\n"
                        f"Current quantity: {stock.quantity}\n"
                        f"Minimum threshold: {stock.min_threshold}\n"
                        f"Office: {stock.item.office.name}\n"
                    ),
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "ims@localhost"),
                    recipient_list=recipients,
                    fail_silently=True,
                )

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `inventory/serializers.py`
```python
from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from actions.models import AssignmentStatus
from .models import (
    ConsumableStock,
    ConsumableStockTransaction,
    FixedAsset,
    InventoryItem,
    InventoryItemType,
    StockTransactionType,
)


class InventoryItemSerializer(serializers.ModelSerializer):
    serial_number = serializers.SerializerMethodField()
    assigned_to = serializers.SerializerMethodField()
    assignment_status = serializers.SerializerMethodField()

    class Meta:
        model = InventoryItem
        fields = [
            "id",
            "category",
            "office",
            "title",
            "item_number",
            "item_type",
            "status",
            "image",
            "amount",
            "price",
            "currency",
            "store",
            "project",
            "department",
            "manufacturer",
            "purchased_date",
            "pi_document",
            "warranty_document",
            "description",
            "dynamic_data",
            "serial_number",
            "assigned_to",
            "assignment_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "serial_number", "assigned_to", "assignment_status", "created_at", "updated_at"]

    def validate(self, attrs):
        category = attrs.get("category", getattr(self.instance, "category", None))
        item_type = attrs.get("item_type", getattr(self.instance, "item_type", None))
        if category and item_type:
            if category.is_consumable and item_type == InventoryItemType.FIXED_ASSET:
                raise serializers.ValidationError({"item_type": "Consumable category requires CONSUMABLE item type."})
            if not category.is_consumable and item_type == InventoryItemType.CONSUMABLE:
                raise serializers.ValidationError({"item_type": "Non-consumable category requires FIXED_ASSET item type."})
        return attrs

    def get_serial_number(self, obj):
        fixed_asset = getattr(obj, "fixed_asset", None)
        return getattr(fixed_asset, "serial_number", None)

    def get_assigned_to(self, obj):
        active_assignment = obj.assignments.filter(status=AssignmentStatus.ASSIGNED).select_related(
            "assigned_to_user", "assigned_to_office"
        ).first()
        if not active_assignment:
            return None
        if active_assignment.assigned_to_user:
            return active_assignment.assigned_to_user.get_full_name() or active_assignment.assigned_to_user.username
        if active_assignment.assigned_to_office:
            return active_assignment.assigned_to_office.name
        return None

    def get_assignment_status(self, obj):
        has_active = obj.assignments.filter(status=AssignmentStatus.ASSIGNED).exists()
        return "ASSIGNED" if has_active else "UNASSIGNED"


class FixedAssetSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        item = attrs.get("item", getattr(self.instance, "item", None))
        if item is None:
            return attrs

        if item.category.is_consumable:
            raise serializers.ValidationError({"item": "Consumable category cannot have FixedAsset subtype."})

        if hasattr(item, "consumable_stock"):
            raise serializers.ValidationError({"item": "InventoryItem cannot be both FixedAsset and ConsumableStock."})
        return attrs

    class Meta:
        model = FixedAsset
        fields = [
            "id",
            "item",
            "asset_tag",
            "serial_number",
            "purchase_date",
            "warranty_expiry_date",
            "invoice_file",
        ]
        read_only_fields = ["id"]


class ConsumableStockSerializer(serializers.ModelSerializer):
    stock_status = serializers.SerializerMethodField()

    def validate(self, attrs):
        item = attrs.get("item", getattr(self.instance, "item", None))
        if item is None:
            return attrs

        if not item.category.is_consumable:
            raise serializers.ValidationError({"item": "Non-consumable category cannot have ConsumableStock subtype."})

        if hasattr(item, "fixed_asset"):
            raise serializers.ValidationError({"item": "InventoryItem cannot be both FixedAsset and ConsumableStock."})
        return attrs

    class Meta:
        model = ConsumableStock
        fields = [
            "id",
            "item",
            "initial_quantity",
            "quantity",
            "min_threshold",
            "reorder_alert_enabled",
            "unit",
            "stock_status",
        ]
        read_only_fields = ["id", "stock_status"]

    def get_stock_status(self, obj):
        if obj.quantity <= 0:
            return "OUT_OF_STOCK"
        if obj.quantity <= obj.min_threshold:
            return "LOW_STOCK"
        return "ON_BOARDED"


class ConsumableStockTransactionSerializer(serializers.ModelSerializer):
    item_name = serializers.SerializerMethodField()
    item_number = serializers.SerializerMethodField()
    performed_by_name = serializers.SerializerMethodField()

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        stock = validated_data["stock"]
        transaction_type = validated_data["transaction_type"]
        quantity = validated_data["quantity"]

        if transaction_type in [StockTransactionType.STOCK_OUT, StockTransactionType.DAMAGE]:
            if stock.quantity < quantity:
                raise serializers.ValidationError({"quantity": "Insufficient stock for this transaction."})
            new_balance = Decimal(stock.quantity) - Decimal(quantity)
        else:
            new_balance = Decimal(stock.quantity) + Decimal(quantity)

        stock.quantity = new_balance
        stock.save(update_fields=["quantity"])

        validated_data["balance_after"] = new_balance
        return super().create(validated_data)

    class Meta:
        model = ConsumableStockTransaction
        fields = [
            "id",
            "stock",
            "transaction_type",
            "quantity",
            "balance_after",
            "status",
            "amount",
            "assigned_to",
            "department",
            "description",
            "image",
            "performed_by",
            "item_name",
            "item_number",
            "performed_by_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "balance_after",
            "performed_by",
            "item_name",
            "item_number",
            "performed_by_name",
            "created_at",
        ]

    def get_item_name(self, obj):
        return obj.stock.item.title

    def get_item_number(self, obj):
        return obj.stock.item.item_number

    def get_performed_by_name(self, obj):
        if not obj.performed_by:
            return None
        return obj.performed_by.get_full_name() or obj.performed_by.username

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `actions/views.py`
```python
import csv
import io

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.models import InventoryActionType
from audit.utils import create_inventory_audit_log
from common.access import scope_queryset_by_user
from common.permissions import IMSAccessPermission
from .models import AssignmentStatus, ItemAssignment
from .serializers import ItemAssignmentSerializer


class ItemAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ItemAssignment.objects.select_related(
        "item",
        "assigned_to_user",
        "assigned_to_office",
        "assigned_by",
    ).all().order_by("id")
    serializer_class = ItemAssignmentSerializer
    filterset_fields = ["item", "assigned_to_user", "assigned_to_office", "status", "assign_till"]
    search_fields = ["item__title", "item__item_number", "assigned_to_user__username", "assigned_to_office__name", "remarks"]
    ordering_fields = ["id", "handover_date", "assign_till", "created_at", "returned_at"]
    ordering = ["-created_at"]
    permission_classes = [IMSAccessPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        return scope_queryset_by_user(queryset, self.request.user, "item__office_id")

    def perform_create(self, serializer):
        assignment = serializer.save(assigned_by=self.request.user)
        create_inventory_audit_log(
            item=assignment.item,
            action_type=InventoryActionType.ASSIGN,
            user=self.request.user,
            after_data={
                "assignment_id": assignment.id,
                "assigned_to_user": assignment.assigned_to_user_id,
                "assigned_to_office": assignment.assigned_to_office_id,
                "status": assignment.status,
                "assign_till": assignment.assign_till.isoformat() if assignment.assign_till else None,
            },
            remarks="Item assigned",
        )

    def perform_update(self, serializer):
        before_instance = self.get_object()
        before = {
            "status": before_instance.status,
            "assigned_to_user": before_instance.assigned_to_user_id,
            "assigned_to_office": before_instance.assigned_to_office_id,
            "returned_at": before_instance.returned_at.isoformat() if before_instance.returned_at else None,
        }
        assignment = serializer.save()
        action_type = InventoryActionType.RETURN if assignment.status == AssignmentStatus.RETURNED else InventoryActionType.ASSIGN
        create_inventory_audit_log(
            item=assignment.item,
            action_type=action_type,
            user=self.request.user,
            before_data=before,
            after_data={
                "status": assignment.status,
                "assigned_to_user": assignment.assigned_to_user_id,
                "assigned_to_office": assignment.assigned_to_office_id,
                "returned_at": assignment.returned_at.isoformat() if assignment.returned_at else None,
            },
            remarks="Item assignment updated",
        )

    @action(detail=False, methods=["get"], url_path="summary-by-assignee")
    def summary_by_assignee(self, request):
        today = timezone.now().date()
        scoped_qs = scope_queryset_by_user(ItemAssignment.objects.all(), request.user, "item__office_id")
        data = list(
            scoped_qs.values(
                "assigned_to_user",
                "assigned_to_user__first_name",
                "assigned_to_user__last_name",
                "assigned_to_user__username",
                "assigned_to_office",
                "assigned_to_office__name",
            )
            .annotate(
                total_items=Count("id"),
                active=Count("id", filter=Q(status=AssignmentStatus.ASSIGNED)),
                overdue=Count(
                    "id",
                    filter=Q(status=AssignmentStatus.ASSIGNED, assign_till__lt=today),
                ),
                returned=Count("id", filter=Q(status=AssignmentStatus.RETURNED)),
            )
            .order_by("assigned_to_user__username", "assigned_to_office__name")
        )
        return Response(data)

    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

        decoded = file_obj.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))
        created_count = 0
        errors = []

        for index, row in enumerate(reader, start=2):
            payload = {
                "item": row.get("item"),
                "assigned_to_user": row.get("assigned_to_user") or None,
                "assigned_to_office": row.get("assigned_to_office") or None,
                "handover_date": row.get("handover_date"),
                "assign_till": row.get("assign_till") or None,
                "handover_condition": row.get("handover_condition") or "GOOD",
                "status": row.get("status") or "ASSIGNED",
                "remarks": row.get("remarks") or "",
            }
            serializer = self.get_serializer(data=payload)
            if serializer.is_valid():
                assignment = serializer.save(assigned_by=request.user)
                create_inventory_audit_log(
                    item=assignment.item,
                    action_type=InventoryActionType.ASSIGN,
                    user=request.user,
                    after_data={
                        "assignment_id": assignment.id,
                        "assigned_to_user": assignment.assigned_to_user_id,
                        "assigned_to_office": assignment.assigned_to_office_id,
                        "status": assignment.status,
                        "assign_till": assignment.assign_till.isoformat() if assignment.assign_till else None,
                    },
                    remarks="Item assigned (bulk import)",
                )
                created_count += 1
            else:
                errors.append({"line": index, "errors": serializer.errors})

        return Response(
            {"created": created_count, "failed": len(errors), "errors": errors},
            status=status.HTTP_200_OK,
        )

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `audit/utils.py`
```python
from audit.models import InventoryActionType, InventoryAuditLog


def create_inventory_audit_log(*, item, action_type, user=None, before_data=None, after_data=None, remarks=""):
    InventoryAuditLog.objects.create(
        item=item,
        action_type=action_type,
        performed_by=user,
        before_data=before_data or {},
        after_data=after_data or {},
        remarks=remarks or "",
    )


def item_snapshot(item):
    return {
        "id": item.id,
        "title": item.title,
        "item_number": item.item_number,
        "status": item.status,
        "item_type": item.item_type,
        "amount": str(item.amount),
        "office_id": item.office_id,
        "category_id": item.category_id,
    }

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `reports/views.py`
```python
from django.db.models import Count, F, Q
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from actions.models import AssignmentStatus, ItemAssignment
from audit.models import InventoryAuditLog
from common.access import scope_queryset_by_user
from hierarchy.models import Office
from inventory.models import ConsumableStock, FixedAsset, InventoryItem, InventoryStatus


class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        item_qs = scope_queryset_by_user(InventoryItem.objects.all(), request.user, "office_id")
        assignment_qs = scope_queryset_by_user(ItemAssignment.objects.all(), request.user, "item__office_id")
        stock_qs = scope_queryset_by_user(ConsumableStock.objects.all(), request.user, "item__office_id")
        fixed_qs = scope_queryset_by_user(FixedAsset.objects.all(), request.user, "item__office_id")
        office_ids = item_qs.values_list("office_id", flat=True).distinct()
        assigned_count = assignment_qs.filter(status=AssignmentStatus.ASSIGNED).values("item_id").distinct().count()
        unassigned_count = max(item_qs.count() - assigned_count, 0)
        data = {
            "total_inventory_items": item_qs.count(),
            "active_inventory_items": item_qs.filter(status=InventoryStatus.ACTIVE).count(),
            "disposed_inventory_items": item_qs.filter(status=InventoryStatus.DISPOSED).count(),
            "fixed_assets": fixed_qs.count(),
            "consumable_stocks": stock_qs.count(),
            "active_assignments": assignment_qs.filter(status=AssignmentStatus.ASSIGNED).count(),
            "returned_assignments": assignment_qs.filter(status=AssignmentStatus.RETURNED).count(),
            "low_stock_items": stock_qs.filter(
                reorder_alert_enabled=True,
                quantity__lte=F("min_threshold"),
            ).count(),
            "assigned_assets": assigned_count,
            "unassigned_assets": unassigned_count,
            "active_offices": Office.objects.filter(id__in=office_ids).count(),
        }
        return Response(data)


class LowStockReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stocks_qs = scope_queryset_by_user(ConsumableStock.objects.all(), request.user, "item__office_id")
        stocks = (
            stocks_qs.select_related("item", "item__office", "item__category")
            .filter(reorder_alert_enabled=True, quantity__lte=F("min_threshold"))
            .order_by("quantity", "id")
        )

        data = [
            {
                "stock_id": stock.id,
                "item_id": stock.item_id,
                "title": stock.item.title,
                "office": stock.item.office.name,
                "category": stock.item.category.name,
                "quantity": stock.quantity,
                "min_threshold": stock.min_threshold,
                "unit": stock.unit,
            }
            for stock in stocks
        ]
        return Response(data)


class AssignmentSummaryByOfficeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        scoped_qs = scope_queryset_by_user(ItemAssignment.objects.all(), request.user, "item__office_id")
        data = list(
            scoped_qs.values("item__office__id", "item__office__name")
            .annotate(
                total=Count("id"),
                active=Count("id", filter=Q(status=AssignmentStatus.ASSIGNED)),
                returned=Count("id", filter=Q(status=AssignmentStatus.RETURNED)),
            )
            .order_by("item__office__name")
        )
        return Response(data)


class RecentInventoryActivitiesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        logs_qs = scope_queryset_by_user(InventoryAuditLog.objects.all(), request.user, "item__office_id")
        logs = (
            logs_qs.select_related("item", "performed_by")
            .all()
            .order_by("-created_at")[:50]
        )
        data = [
            {
                "id": log.id,
                "item_name": log.item.title,
                "unique_number": log.item.item_number,
                "performed_by": (log.performed_by.get_full_name() or log.performed_by.username) if log.performed_by else None,
                "date": log.created_at.date(),
                "amount": str(log.item.amount),
                "status": log.action_type,
                "action": log.remarks,
            }
            for log in logs
        ]
        return Response(data)


class InventoryReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self, request):
        queryset = scope_queryset_by_user(InventoryItem.objects.all(), request.user, "office_id").select_related("category", "office").order_by("-created_at")
        category = request.query_params.get("category")
        status = request.query_params.get("status")
        office = request.query_params.get("office")
        fiscal_year = request.query_params.get("fiscal_year")

        if category:
            queryset = queryset.filter(category_id=category)
        if status:
            queryset = queryset.filter(status=status)
        if office:
            queryset = queryset.filter(office_id=office)

        # Fiscal year format: YYYY-YYYY, window from Jul 16 first year to Jul 15 second year.
        if fiscal_year and "-" in fiscal_year:
            start_year, end_year = fiscal_year.split("-", 1)
            if start_year.isdigit() and end_year.isdigit():
                queryset = queryset.filter(
                    purchased_date__gte=f"{start_year}-07-16",
                    purchased_date__lte=f"{end_year}-07-15",
                )

        return queryset

    def get(self, request):
        queryset = self.get_queryset(request)
        data = self.serialize_items(queryset)
        return Response(data)

    @staticmethod
    def serialize_items(queryset):
        return [
            {
                "id": item.id,
                "item_name": item.title,
                "item_number": item.item_number,
                "item_type": item.item_type,
                "category": item.category.name,
                "office": item.office.name,
                "status": item.status,
                "amount": str(item.amount),
                "purchased_date": item.purchased_date,
            }
            for item in queryset
        ]


class InventoryReportExportCSVView(InventoryReportView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = self.get_queryset(request)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="inventory_report.csv"'
        response.write("item_name,item_number,item_type,category,office,status,amount,purchased_date\n")
        for item in queryset:
            response.write(
                f'"{item.title}","{item.item_number or ""}","{item.item_type}","{item.category.name}","{item.office.name}","{item.status}","{item.amount}","{item.purchased_date or ""}"\n'
            )
        return response


class InventoryReportExportExcelView(InventoryReportView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = self.get_queryset(request)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Inventory Report"

        headers = ["Item Name", "Item Number", "Item Type", "Category", "Office", "Status", "Amount", "Purchased Date"]
        sheet.append(headers)

        for item in queryset:
            sheet.append(
                [
                    item.title,
                    item.item_number or "",
                    item.item_type,
                    item.category.name,
                    item.office.name,
                    item.status,
                    float(item.amount),
                    item.purchased_date.isoformat() if item.purchased_date else "",
                ]
            )

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="inventory_report.xlsx"'
        workbook.save(response)
        return response


class InventoryReportExportPDFView(InventoryReportView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = self.get_queryset(request)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="inventory_report.pdf"'

        pdf = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        y = height - 40

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, "DoNIDCR - Inventory Report")
        y -= 20

        pdf.setFont("Helvetica", 9)
        pdf.drawString(40, y, "Item Name")
        pdf.drawString(210, y, "Item Number")
        pdf.drawString(300, y, "Category")
        pdf.drawString(390, y, "Office")
        pdf.drawString(480, y, "Status")
        y -= 14

        for item in queryset:
            if y < 50:
                pdf.showPage()
                y = height - 40
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(40, y, "DoNIDCR - Inventory Report (cont.)")
                y -= 20
                pdf.setFont("Helvetica", 9)

            pdf.drawString(40, y, (item.title or "")[:28])
            pdf.drawString(210, y, (item.item_number or "")[:14])
            pdf.drawString(300, y, (item.category.name or "")[:14])
            pdf.drawString(390, y, (item.office.name or "")[:14])
            pdf.drawString(480, y, (item.status or "")[:10])
            y -= 14

        pdf.save()
        return response

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `common/access.py`
```python
from users.models import UserRoles
from hierarchy.models import Office


GLOBAL_ROLES = {
    UserRoles.SUPER_ADMIN,
    UserRoles.CENTRAL_ADMIN,
    UserRoles.CENTRAL_PROCUREMENT_STORE,
    UserRoles.FINANCE,
    UserRoles.AUDIT,
}

SCOPED_ROLES = {
    UserRoles.PROVINCIAL_ADMIN,
    UserRoles.LOCAL_ADMIN,
    UserRoles.WARD_OFFICER,
}


def get_descendant_office_ids(root_office_id):
    if not root_office_id:
        return []
    office_ids = {root_office_id}
    frontier = {root_office_id}
    while frontier:
        child_ids = set(
            Office.objects.filter(parent_office_id__in=frontier).values_list("id", flat=True)
        ) - office_ids
        if not child_ids:
            break
        office_ids.update(child_ids)
        frontier = child_ids
    return list(office_ids)


def get_accessible_office_ids(user):
    if user.is_staff or user.is_superuser:
        return None
    if user.role in GLOBAL_ROLES:
        return None
    if user.role in SCOPED_ROLES:
        if user.role == UserRoles.WARD_OFFICER:
            return [user.office_id] if user.office_id else []
        return get_descendant_office_ids(user.office_id)
    return []


def scope_queryset_by_user(queryset, user, office_lookup):
    office_ids = get_accessible_office_ids(user)
    if office_ids is None:
        return queryset
    return queryset.filter(**{f"{office_lookup}__in": office_ids})

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `common/management/commands/seed_prd_data.py`
```python
from datetime import date, datetime, timezone
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from actions.models import AssignmentStatus, ItemAssignment, ItemCondition
from audit.models import InventoryActionType, InventoryAuditLog
from catalog.models import Category, CustomFieldDefinition, CustomFieldType
from hierarchy.models import Office, OfficeLevels
from inventory.models import (
    ConsumableStock,
    ConsumableStockTransaction,
    FixedAsset,
    InventoryItem,
    InventoryItemType,
    InventoryStatus,
    StockTransactionType,
)
from users.models import User, UserRoles


OFFICES = [
    ("DoNIDCR Central Office", OfficeLevels.CENTRAL, None, "NPL-CENTRAL-001"),
    ("Province 1 Office", OfficeLevels.PROVINCIAL, "NPL-CENTRAL-001", "NPL-P1-001"),
    ("Province 2 Office", OfficeLevels.PROVINCIAL, "NPL-CENTRAL-001", "NPL-P2-001"),
    ("Kathmandu Metropolitan Office", OfficeLevels.LOCAL, "NPL-P1-001", "NPL-L1-001"),
    ("Lalitpur Metropolitan Office", OfficeLevels.LOCAL, "NPL-P1-001", "NPL-L1-002"),
    ("Ward 1 Registration Point", OfficeLevels.WARD, "NPL-L1-001", "NPL-W1-001"),
    ("Ward 2 Registration Point", OfficeLevels.WARD, "NPL-L1-001", "NPL-W1-002"),
]

USERS = [
    ("superadmin", "SUPER_ADMIN", True, "NPL-CENTRAL-001"),
    ("central_admin", "CENTRAL_ADMIN", True, "NPL-CENTRAL-001"),
    ("store_keeper", "CENTRAL_PROCUREMENT_STORE", False, "NPL-CENTRAL-001"),
    ("prov_admin_p1", "PROVINCIAL_ADMIN", False, "NPL-P1-001"),
    ("local_admin_ktm", "LOCAL_ADMIN", False, "NPL-L1-001"),
    ("ward_officer_1", "WARD_OFFICER", False, "NPL-W1-001"),
    ("finance_user", "FINANCE", False, "NPL-CENTRAL-001"),
    ("audit_user", "AUDIT", False, "NPL-CENTRAL-001"),
]

CUSTOM_FIELDS = [
    ("Laptop", "RAM", CustomFieldType.SELECT, True, False, ["8GB", "16GB", "32GB"]),
    ("Laptop", "Processor", CustomFieldType.TEXT, True, False, []),
    ("Laptop", "Storage", CustomFieldType.SELECT, True, False, ["256GB SSD", "512GB SSD", "1TB SSD"]),
    ("Printer", "Model", CustomFieldType.TEXT, True, False, []),
    ("Printer", "Ink Type", CustomFieldType.SELECT, True, False, ["Inkjet", "Laser Toner"]),
    ("Biometric Device", "Vendor", CustomFieldType.TEXT, True, False, []),
    ("Registration Forms", "Form Type", CustomFieldType.SELECT, True, False, ["Birth", "Death", "Marriage"]),
    ("Stationery", "Unit", CustomFieldType.TEXT, True, False, []),
    ("Toner/Ink", "Color", CustomFieldType.SELECT, False, False, ["Black", "Cyan", "Magenta", "Yellow"]),
]

ITEMS = [
    {
        "item_number": "FA-0001",
        "title": "Dell Latitude 5440",
        "category": "Laptop",
        "office_code": "NPL-W1-001",
        "item_type": InventoryItemType.FIXED_ASSET,
        "status": InventoryStatus.ACTIVE,
        "amount": Decimal("120000.00"),
        "price": Decimal("120000.00"),
        "currency": "NPR",
        "department": "Registration",
        "manufacturer": "Dell",
        "purchased_date": date(2025, 7, 20),
        "dynamic_data": {"RAM": "16GB", "Processor": "Intel i7", "Storage": "512GB SSD"},
        "fixed_asset": {
            "asset_tag": "LAP-W1-0001",
            "serial_number": "SN-LAP-0001",
            "purchase_date": date(2025, 7, 20),
            "warranty_expiry_date": date(2028, 7, 20),
        },
    },
    {
        "item_number": "FA-0002",
        "title": "HP LaserJet Pro",
        "category": "Printer",
        "office_code": "NPL-L1-001",
        "item_type": InventoryItemType.FIXED_ASSET,
        "status": InventoryStatus.ACTIVE,
        "amount": Decimal("45000.00"),
        "price": Decimal("45000.00"),
        "currency": "NPR",
        "department": "Office Operations",
        "manufacturer": "HP",
        "purchased_date": date(2025, 8, 10),
        "dynamic_data": {"Model": "M404dn", "Ink Type": "Laser Toner"},
        "fixed_asset": {
            "asset_tag": "PRN-L1-0001",
            "serial_number": "SN-PRN-0001",
            "purchase_date": date(2025, 8, 10),
            "warranty_expiry_date": date(2027, 8, 10),
        },
    },
    {
        "item_number": "CON-0001",
        "title": "Citizen Registration Form",
        "category": "Registration Forms",
        "office_code": "NPL-W1-001",
        "item_type": InventoryItemType.CONSUMABLE,
        "status": InventoryStatus.ACTIVE,
        "amount": Decimal("10000.00"),
        "price": Decimal("10.00"),
        "currency": "NPR",
        "department": "Registration",
        "manufacturer": "Govt Printing Press",
        "purchased_date": date(2025, 7, 25),
        "dynamic_data": {"Form Type": "Birth"},
        "consumable_stock": {
            "initial_quantity": Decimal("1000"),
            "quantity": Decimal("920"),
            "min_threshold": Decimal("200"),
            "unit": "pcs",
        },
    },
    {
        "item_number": "CON-0002",
        "title": "A4 Office Paper",
        "category": "Stationery",
        "office_code": "NPL-L1-001",
        "item_type": InventoryItemType.CONSUMABLE,
        "status": InventoryStatus.ACTIVE,
        "amount": Decimal("15000.00"),
        "price": Decimal("500.00"),
        "currency": "NPR",
        "department": "Admin",
        "manufacturer": "Nepal Paper Co",
        "purchased_date": date(2025, 9, 1),
        "dynamic_data": {"Unit": "ream"},
        "consumable_stock": {
            "initial_quantity": Decimal("100"),
            "quantity": Decimal("60"),
            "min_threshold": Decimal("20"),
            "unit": "ream",
        },
    },
]


class Command(BaseCommand):
    help = "Seed PRD-aligned sample data across core IMS tables (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing data.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        self.stdout.write("Seeding PRD-aligned data...")

        with transaction.atomic():
            call_command("seed_initial_categories", dry_run=dry_run, stdout=self.stdout)

            offices = self._seed_offices(dry_run=dry_run)
            users = self._seed_users(offices=offices, dry_run=dry_run)
            self._seed_custom_fields(dry_run=dry_run)
            items = self._seed_inventory(offices=offices, dry_run=dry_run)
            self._seed_assignments(items=items, users=users, offices=offices, dry_run=dry_run)
            self._seed_stock_transactions(items=items, users=users, dry_run=dry_run)
            self._seed_audit_logs(items=items, users=users, dry_run=dry_run)

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("Dry run enabled. Rolled back all changes."))

        self.stdout.write(self.style.SUCCESS("PRD seed completed."))

    def _seed_offices(self, dry_run=False):
        office_by_code = {o.location_code: o for o in Office.objects.all()}
        created = 0
        updated = 0

        for name, level, parent_code, code in OFFICES:
            parent = office_by_code.get(parent_code) if parent_code else None
            obj = Office.objects.filter(location_code=code).first()
            if obj is None:
                created += 1
                if not dry_run:
                    obj = Office.objects.create(name=name, level=level, parent_office=parent, location_code=code)
                office_by_code[code] = obj
                self.stdout.write(self.style.SUCCESS(f"{'Would create' if dry_run else 'Created'} office: {code}"))
                continue

            changed = False
            if obj.name != name:
                obj.name = name
                changed = True
            if obj.level != level:
                obj.level = level
                changed = True
            if obj.parent_office_id != (parent.id if parent else None):
                obj.parent_office = parent
                changed = True
            if changed:
                updated += 1
                if not dry_run:
                    obj.save(update_fields=["name", "level", "parent_office"])
                self.stdout.write(self.style.WARNING(f"{'Would update' if dry_run else 'Updated'} office: {code}"))
            office_by_code[code] = obj

        self.stdout.write(f"Offices: created={created}, updated={updated}, total={len(office_by_code)}")
        return office_by_code

    def _seed_users(self, offices, dry_run=False):
        users = {}
        created = 0
        updated = 0

        for username, role, is_staff, office_code in USERS:
            office = offices.get(office_code)
            defaults = {
                "email": f"{username}@ims.local",
                "first_name": username.replace("_", " ").title(),
                "role": role,
                "is_staff": is_staff,
                "is_active": True,
                "office": office,
            }
            obj = User.objects.filter(username=username).first()
            if obj is None:
                created += 1
                if not dry_run:
                    obj = User.objects.create(username=username, **defaults)
                    obj.set_password("ChangeMe123!")
                    obj.save(update_fields=["password"])
                self.stdout.write(self.style.SUCCESS(f"{'Would create' if dry_run else 'Created'} user: {username}"))
            else:
                changed = False
                for field, value in defaults.items():
                    if getattr(obj, field) != value:
                        setattr(obj, field, value)
                        changed = True
                if changed and not dry_run:
                    obj.save(update_fields=list(defaults.keys()))
                if changed:
                    updated += 1
                    self.stdout.write(self.style.WARNING(f"{'Would update' if dry_run else 'Updated'} user: {username}"))
            users[username] = obj

        self.stdout.write(f"Users: created={created}, updated={updated}, total={len(users)}")
        return users

    def _seed_custom_fields(self, dry_run=False):
        created = 0
        updated = 0
        skipped = 0
        for category_name, label, field_type, required, is_unique, select_options in CUSTOM_FIELDS:
            category = Category.objects.filter(name=category_name).first()
            if not category:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"Skipped custom field '{label}': category '{category_name}' not found"))
                continue

            obj = CustomFieldDefinition.objects.filter(category=category, label=label).first()
            if obj is None:
                created += 1
                if not dry_run:
                    CustomFieldDefinition.objects.create(
                        category=category,
                        label=label,
                        field_type=field_type,
                        required=required,
                        is_unique=is_unique,
                        select_options=select_options,
                    )
                self.stdout.write(self.style.SUCCESS(f"{'Would create' if dry_run else 'Created'} custom field: {category_name}::{label}"))
            else:
                changed = False
                if obj.field_type != field_type:
                    obj.field_type = field_type
                    changed = True
                if obj.required != required:
                    obj.required = required
                    changed = True
                if obj.is_unique != is_unique:
                    obj.is_unique = is_unique
                    changed = True
                if obj.select_options != select_options:
                    obj.select_options = select_options
                    changed = True
                if changed:
                    updated += 1
                    if not dry_run:
                        obj.save(update_fields=["field_type", "required", "is_unique", "select_options"])
                    self.stdout.write(self.style.WARNING(f"{'Would update' if dry_run else 'Updated'} custom field: {category_name}::{label}"))

        self.stdout.write(f"Custom fields: created={created}, updated={updated}, skipped={skipped}")

    def _seed_inventory(self, offices, dry_run=False):
        item_by_number = {}
        created = 0
        updated = 0

        for payload in ITEMS:
            category = Category.objects.get(name=payload["category"])
            office = offices[payload["office_code"]]
            defaults = {
                "title": payload["title"],
                "category": category,
                "office": office,
                "item_type": payload["item_type"],
                "status": payload["status"],
                "amount": payload["amount"],
                "price": payload["price"],
                "currency": payload["currency"],
                "department": payload["department"],
                "manufacturer": payload["manufacturer"],
                "purchased_date": payload["purchased_date"],
                "dynamic_data": payload["dynamic_data"],
            }

            obj = InventoryItem.objects.filter(item_number=payload["item_number"]).first()
            if obj is None:
                created += 1
                if not dry_run:
                    obj = InventoryItem.objects.create(item_number=payload["item_number"], **defaults)
                self.stdout.write(self.style.SUCCESS(f"{'Would create' if dry_run else 'Created'} item: {payload['item_number']}"))
            else:
                changed = False
                for field, value in defaults.items():
                    if getattr(obj, field) != value:
                        setattr(obj, field, value)
                        changed = True
                if changed:
                    updated += 1
                    if not dry_run:
                        obj.save(update_fields=list(defaults.keys()))
                    self.stdout.write(self.style.WARNING(f"{'Would update' if dry_run else 'Updated'} item: {payload['item_number']}"))

            if payload["item_type"] == InventoryItemType.FIXED_ASSET:
                fa_defaults = payload["fixed_asset"]
                if not dry_run and obj:
                    FixedAsset.objects.update_or_create(item=obj, defaults=fa_defaults)
            else:
                stock_defaults = payload["consumable_stock"]
                if not dry_run and obj:
                    ConsumableStock.objects.update_or_create(item=obj, defaults=stock_defaults)

            item_by_number[payload["item_number"]] = obj

        self.stdout.write(f"Inventory items: created={created}, updated={updated}, total={len(item_by_number)}")
        return item_by_number

    def _seed_assignments(self, items, users, offices, dry_run=False):
        assigned_item = items.get("FA-0001")
        returned_item = items.get("FA-0002")
        assigned_by = users.get("store_keeper")
        assigned_user = users.get("ward_officer_1")
        assigned_office = offices.get("NPL-L1-001")

        if not dry_run and assigned_item and assigned_by and assigned_user:
            ItemAssignment.objects.update_or_create(
                item=assigned_item,
                status=AssignmentStatus.ASSIGNED,
                defaults={
                    "assigned_to_user": assigned_user,
                    "assigned_to_office": None,
                    "assigned_by": assigned_by,
                    "handover_date": date(2025, 8, 1),
                    "assign_till": date(2026, 8, 1),
                    "handover_condition": ItemCondition.GOOD,
                    "remarks": "PRD seed: assigned laptop to ward officer",
                },
            )

        if not dry_run and returned_item and assigned_by and assigned_office:
            ItemAssignment.objects.update_or_create(
                item=returned_item,
                status=AssignmentStatus.RETURNED,
                defaults={
                    "assigned_to_user": None,
                    "assigned_to_office": assigned_office,
                    "assigned_by": assigned_by,
                    "handover_date": date(2025, 8, 12),
                    "assign_till": date(2025, 12, 31),
                    "returned_at": datetime(2025, 12, 20, 10, 30, tzinfo=timezone.utc),
                    "return_condition": ItemCondition.GOOD,
                    "handover_condition": ItemCondition.GOOD,
                    "remarks": "PRD seed: printer returned in good condition",
                },
            )

        self.stdout.write("Assignments: upserted 2 sample records")

    def _seed_stock_transactions(self, items, users, dry_run=False):
        if dry_run:
            self.stdout.write("Stock transactions: would upsert 2 sample records")
            return

        stock_item = items.get("CON-0001")
        performer = users.get("store_keeper")
        assignee = users.get("ward_officer_1")
        if not stock_item:
            self.stdout.write(self.style.WARNING("Stock transactions skipped: CON-0001 item not found"))
            return
        stock = ConsumableStock.objects.filter(item=stock_item).first()
        if not stock:
            self.stdout.write(self.style.WARNING("Stock transactions skipped: stock row for CON-0001 not found"))
            return

        in_txn, _ = ConsumableStockTransaction.objects.get_or_create(
            stock=stock,
            transaction_type=StockTransactionType.STOCK_IN,
            description="PRD seed opening stock adjustment",
            defaults={
                "quantity": Decimal("1000"),
                "balance_after": Decimal("1000"),
                "status": "COMPLETED",
                "amount": Decimal("10000"),
                "assigned_to": None,
                "performed_by": performer,
                "department": "Central Store",
            },
        )
        out_txn, _ = ConsumableStockTransaction.objects.get_or_create(
            stock=stock,
            transaction_type=StockTransactionType.STOCK_OUT,
            description="PRD seed issued to ward office",
            defaults={
                "quantity": Decimal("80"),
                "balance_after": Decimal("920"),
                "status": "COMPLETED",
                "amount": Decimal("800"),
                "assigned_to": assignee,
                "performed_by": performer,
                "department": "Ward Services",
            },
        )

        final_balance = out_txn.balance_after if out_txn else in_txn.balance_after
        if stock.quantity != final_balance:
            stock.quantity = final_balance
            stock.save(update_fields=["quantity"])

        self.stdout.write("Stock transactions: upserted 2 sample records")

    def _seed_audit_logs(self, items, users, dry_run=False):
        if dry_run:
            self.stdout.write("Audit logs: would upsert sample records")
            return

        actor = users.get("store_keeper")
        for item_number, item in items.items():
            if not item:
                continue
            InventoryAuditLog.objects.get_or_create(
                item=item,
                action_type=InventoryActionType.CREATE,
                remarks=f"PRD seed: created {item_number}",
                defaults={
                    "performed_by": actor,
                    "before_data": {},
                    "after_data": {
                        "item_number": item.item_number,
                        "title": item.title,
                        "status": item.status,
                        "item_type": item.item_type,
                    },
                },
            )

        assigned_item = items.get("FA-0001")
        returned_item = items.get("FA-0002")

        if assigned_item:
            InventoryAuditLog.objects.get_or_create(
                item=assigned_item,
                action_type=InventoryActionType.ASSIGN,
                remarks="PRD seed: assignment recorded",
                defaults={
                    "performed_by": actor,
                    "after_data": {"status": "ASSIGNED"},
                },
            )
        if returned_item:
            InventoryAuditLog.objects.get_or_create(
                item=returned_item,
                action_type=InventoryActionType.RETURN,
                remarks="PRD seed: return recorded",
                defaults={
                    "performed_by": actor,
                    "after_data": {"status": "RETURNED"},
                },
            )

        self.stdout.write("Audit logs: upserted sample records")

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `catalog/management/commands/seed_initial_categories.py`
```python
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Category


FIXED_ASSET_CATEGORIES = [
    "Laptop",
    "Desktop",
    "Printer",
    "Scanner",
    "Biometric Device",
    "Furniture",
    "Networking Equipment",
    "UPS/Inverter",
    "Server/Storage",
    "CCTV/Access Device",
]

CONSUMABLE_CATEGORIES = [
    "Registration Forms",
    "Stationery",
    "Toner/Ink",
    "Printer Ribbon",
    "Batteries",
    "Cables/Connectors",
    "Cleaning/Repair Consumables",
    "ID Card Consumables",
]


class Command(BaseCommand):
    help = "Seed initial PRD-based catalog categories (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without writing to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        created = 0
        updated = 0
        unchanged = 0

        targets = [(name, False) for name in FIXED_ASSET_CATEGORIES] + [
            (name, True) for name in CONSUMABLE_CATEGORIES
        ]

        with transaction.atomic():
            for name, is_consumable in targets:
                obj = Category.objects.filter(name=name).first()
                if obj is None:
                    created += 1
                    if not dry_run:
                        Category.objects.create(name=name, is_consumable=is_consumable)
                    self.stdout.write(self.style.SUCCESS(f"{'Would create' if dry_run else 'Created'}: {name}"))
                    continue

                if obj.is_consumable != is_consumable:
                    updated += 1
                    if not dry_run:
                        obj.is_consumable = is_consumable
                        obj.save(update_fields=["is_consumable"])
                    self.stdout.write(self.style.WARNING(f"{'Would update' if dry_run else 'Updated'}: {name}"))
                else:
                    unchanged += 1
                    self.stdout.write(f"Unchanged: {name}")

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("Dry run enabled. Rolled back all changes."))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. created={created}, updated={updated}, unchanged={unchanged}, dry_run={dry_run}"
            )
        )

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

## Rebuild Step (Hands-on Roadmap)
- Implement or review the files listed in this chapter only.
- Validate behavior discussed in the original chapter explanation.
- Confirm readiness for the next chapter transition.

## Chapter Summary
This chapter ties repository explanation to exact code references and prepares the next build step.

## Files Used
- `inventory/views.py`
- `inventory/serializers.py`
- `actions/views.py`
- `audit/utils.py`
- `reports/views.py`
- `common/access.py`
- `common/management/commands/seed_prd_data.py`
- `catalog/management/commands/seed_initial_categories.py`

