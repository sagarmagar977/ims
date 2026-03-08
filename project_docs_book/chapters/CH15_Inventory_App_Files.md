# Chapter 15 — Inventory App Files

## Build Roadmap Position
- Stage: Core Domain
- You are here: Chapter 15
- Before this: Chapter 14
- After this: Chapter 16

## Learning Objectives
- Understand inventory domain entities and their relationships.
- Learn inventory API behavior, validation rules, and side effects.
- Map migration evolution of inventory features.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 15 — Inventory App Files

## Learning Goals
- Understand inventory domain entities and their relationships.
- Learn inventory API behavior, validation rules, and side effects.
- Map migration evolution of inventory features.

## Reference Files
- `inventory/models.py`
- `inventory/serializers.py`
- `inventory/views.py`
- `inventory/urls.py`
- `inventory/tests.py`
- `inventory/admin.py`
- `inventory/apps.py`
- `inventory/migrations/0001_initial.py`
- `inventory/migrations/0002_consumablestock_initial_quantity_and_more.py`
- `inventory/migrations/0003_consumablestocktransaction_inventoryitem_amount_and_more.py`

## File Breakdown

## 1) `inventory/models.py`
### Core enums
- `InventoryStatus`: `ACTIVE`, `INACTIVE`, `DISPOSED`, `ASSIGNED`, `UNASSIGNED`
- `InventoryItemType`: `FIXED_ASSET`, `CONSUMABLE`
- `StockTransactionType`: `STOCK_IN`, `STOCK_OUT`, `DAMAGE`, `ADJUSTMENT`

### `InventoryItem`
- Main inventory entity with category + office FK.
- Rich metadata fields:
  - identity (`title`, `item_number`, `item_type`, `status`)
  - financial (`amount`, `price`, `currency`)
  - operational (`store`, `project`, `department`, `manufacturer`)
  - document/media fields (`image`, `pi_document`, `warranty_document`)
  - `dynamic_data` JSON for flexible attributes.
- Integrity checks in `clean()` prevent incompatible subtype combinations.
- Indexed on category/office, status, and item_number.

### `FixedAsset`
- One-to-one subtype for fixed assets.
- Includes asset/serial/warranty/invoice fields.

### `ConsumableStock`
- One-to-one subtype for consumables.
- Tracks initial quantity, current quantity, threshold, alert flag, unit.

### `ConsumableStockTransaction`
- Event-style stock movement table.
- Stores transaction type, quantity, resulting balance, status/amount, assignee/performer, department/description/image.
- Indexed by stock+time and transaction type.

## 2) `inventory/serializers.py`
### `InventoryItemSerializer`
- Enforces category/type compatibility in `validate`.
- Exposes computed fields:
  - `serial_number` (from fixed asset)
  - `assigned_to` and `assignment_status` (from active assignments)

### `FixedAssetSerializer` / `ConsumableStockSerializer`
- Enforce subtype exclusivity and category compatibility.
- `ConsumableStockSerializer` adds computed `stock_status` (`OUT_OF_STOCK`, `LOW_STOCK`, `ON_BOARDED`).

### `ConsumableStockTransactionSerializer`
- Validates positive quantity.
- `create()` uses `@transaction.atomic` to:
  - adjust stock quantity by transaction type,
  - prevent insufficient stock for out/damage,
  - persist `balance_after`.
- Adds computed read fields for item and performer names.

## 3) `inventory/views.py`
### ViewSets
- `InventoryItemViewSet`
- `FixedAssetViewSet`
- `ConsumableStockViewSet`
- `ConsumableStockTransactionViewSet`

Shared behavior:
- `IMSAccessPermission` enforced.
- Querysets scoped by office access using `scope_queryset_by_user`.
- Filter/search/order fields configured per resource.

### Inventory item side effects
- `perform_create` / `perform_update` create audit logs with snapshots.

### Bulk import
- `InventoryItemViewSet.bulk_import` accepts CSV upload.
- Per-row validation/save; per-row audit on success.
- Returns summary (`created`, `failed`, `errors`).

### Stock transaction side effects
- `perform_create` sets `performed_by`, writes audit log.
- Sends low-stock email alert when threshold condition and recipients are present.

## 4) `inventory/urls.py`
Router endpoints:
- `inventory-items`
- `fixed-assets`
- `consumable-stocks`
- `consumable-stock-transactions`

These are reachable under both `/api/` and `/api/v1/` via root URL includes.

## 5) `inventory/tests.py`
`InventoryAccessAndTransactionTests` validates:
- scoped visibility by office hierarchy,
- read-only finance role restrictions,
- ward write restrictions for inventory create,
- stock transaction balance mutation,
- audit creation on inventory bulk import.

## 6) `inventory/admin.py`
Registers:
- `InventoryItem`
- `FixedAsset`
- `ConsumableStock`
- `ConsumableStockTransaction`

## 7) `inventory/apps.py`
Declares `InventoryConfig` with `name='inventory'`.

## 8) Migration Evolution
- `0001_initial.py`:
  - introduces base inventory entities (`InventoryItem`, `FixedAsset`, `ConsumableStock`) and core indexes.
- `0002_*`:
  - extends stock and fixed-asset fields (`initial_quantity`, `min_threshold`, `reorder_alert_enabled`, `serial_number`, warranty/invoice fields).
- `0003_*`:
  - adds `ConsumableStockTransaction` model.
  - significantly expands `InventoryItem` fields.
  - adds `item_type`, `item_number`, additional statuses, and indexes.
  - links transactions to users (`assigned_to`, `performed_by`).

## Inventory App Responsibilities (Observed)
- central asset/stock domain model.
- subtype-specific handling for fixed vs consumable items.
- stock movement accounting with transactional consistency.
- operational side effects: audit logging, low-stock notifications.

## Architecture Notes
- Inventory is a high-coupling core module used by actions, audit, and reports.
- Data integrity is enforced across model constraints, serializer validation, and transactional logic.
- Flexible item metadata is supported through `dynamic_data` plus catalog custom fields.

## Chapter 15 Outcome
You now have a complete inventory-app map: domain schema, API behavior, validation and transaction safeguards, audit/notification side effects, and migration-based feature growth.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
### File: `inventory/models.py`
```python
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models

from catalog.models import Category
from hierarchy.models import Office


class InventoryStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    DISPOSED = "DISPOSED", "Disposed"
    ASSIGNED = "ASSIGNED", "Assigned"
    UNASSIGNED = "UNASSIGNED", "Unassigned"


class InventoryItemType(models.TextChoices):
    FIXED_ASSET = "FIXED_ASSET", "Fixed Asset"
    CONSUMABLE = "CONSUMABLE", "Consumable"


class InventoryItem(models.Model):
    category = models.ForeignKey(Category, related_name="items", on_delete=models.PROTECT)
    office = models.ForeignKey(Office, related_name="items", on_delete=models.PROTECT)

    title = models.CharField(max_length=255)
    item_number = models.CharField(max_length=64, unique=True, null=True, blank=True)
    item_type = models.CharField(max_length=16, choices=InventoryItemType.choices, default=InventoryItemType.FIXED_ASSET)
    status = models.CharField(max_length=16, choices=InventoryStatus.choices, default=InventoryStatus.ACTIVE)
    image = models.FileField(upload_to="inventory/images/", null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=16, blank=True)
    store = models.CharField(max_length=128, blank=True)
    project = models.CharField(max_length=128, blank=True)
    department = models.CharField(max_length=128, blank=True)
    manufacturer = models.CharField(max_length=128, blank=True)
    purchased_date = models.DateField(null=True, blank=True)
    pi_document = models.FileField(upload_to="inventory/pi_documents/", null=True, blank=True)
    warranty_document = models.FileField(upload_to="inventory/warranty_documents/", null=True, blank=True)
    description = models.TextField(blank=True)
    dynamic_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["category", "office"]),
            models.Index(fields=["status"]),
            models.Index(fields=["item_number"]),
        ]

    def clean(self):
        super().clean()

        if self.pk:
            has_fixed = hasattr(self, "fixed_asset")
            has_consumable = hasattr(self, "consumable_stock")

            if has_fixed and has_consumable:
                raise ValidationError("InventoryItem cannot be both FixedAsset and ConsumableStock.")

            if self.category_id:
                if self.category.is_consumable and has_fixed:
                    raise ValidationError("Consumable category cannot have FixedAsset subtype.")
                if not self.category.is_consumable and has_consumable:
                    raise ValidationError("Non-consumable category cannot have ConsumableStock subtype.")

    def __str__(self) -> str:
        return f"{self.title} @ {self.office}"


class FixedAsset(models.Model):
    item = models.OneToOneField(
        InventoryItem,
        related_name="fixed_asset",
        on_delete=models.CASCADE,
    )
    asset_tag = models.CharField(max_length=64, blank=True)
    serial_number = models.CharField(max_length=128, unique=True, null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    warranty_expiry_date = models.DateField(null=True, blank=True)
    invoice_file = models.FileField(upload_to="inventory/invoices/", null=True, blank=True)

    def __str__(self) -> str:
        return f"FixedAsset: {self.item.title}"


class ConsumableStock(models.Model):
    item = models.OneToOneField(
        InventoryItem,
        related_name="consumable_stock",
        on_delete=models.CASCADE,
    )
    initial_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    min_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_alert_enabled = models.BooleanField(default=True)
    unit = models.CharField(max_length=32, default="pcs")

    def __str__(self) -> str:
        return f"ConsumableStock: {self.item.title} ({self.quantity} {self.unit})"


class StockTransactionType(models.TextChoices):
    STOCK_IN = "STOCK_IN", "Stock In"
    STOCK_OUT = "STOCK_OUT", "Stock Out"
    DAMAGE = "DAMAGE", "Damage"
    ADJUSTMENT = "ADJUSTMENT", "Adjustment"


class ConsumableStockTransaction(models.Model):
    stock = models.ForeignKey(ConsumableStock, related_name="transactions", on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=16, choices=StockTransactionType.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=32, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="stock_transactions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    department = models.CharField(max_length=128, blank=True)
    description = models.TextField(blank=True)
    image = models.FileField(upload_to="inventory/stock_transactions/", null=True, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="performed_stock_transactions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["stock", "created_at"]),
            models.Index(fields=["transaction_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.stock.item.title} - {self.transaction_type} ({self.quantity})"

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

### File: `inventory/urls.py`
```python
from rest_framework.routers import DefaultRouter

from .views import ConsumableStockTransactionViewSet, ConsumableStockViewSet, FixedAssetViewSet, InventoryItemViewSet

router = DefaultRouter()
router.register(r"inventory-items", InventoryItemViewSet, basename="inventory-item")
router.register(r"fixed-assets", FixedAssetViewSet, basename="fixed-asset")
router.register(r"consumable-stocks", ConsumableStockViewSet, basename="consumable-stock")
router.register(r"consumable-stock-transactions", ConsumableStockTransactionViewSet, basename="consumable-stock-transaction")

urlpatterns = router.urls

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `inventory/tests.py`
```python
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from audit.models import InventoryActionType, InventoryAuditLog
from catalog.models import Category
from hierarchy.models import Office, OfficeLevels
from users.models import User, UserRoles

from .models import ConsumableStock, InventoryItem, InventoryItemType


class InventoryAccessAndTransactionTests(APITestCase):
    def setUp(self):
        self.central = Office.objects.create(name="Central", level=OfficeLevels.CENTRAL, location_code="C-1")
        self.province_1 = Office.objects.create(
            name="Province 1", level=OfficeLevels.PROVINCIAL, parent_office=self.central, location_code="P1"
        )
        self.province_2 = Office.objects.create(
            name="Province 2", level=OfficeLevels.PROVINCIAL, parent_office=self.central, location_code="P2"
        )
        self.ward_11 = Office.objects.create(
            name="Ward 11", level=OfficeLevels.WARD, parent_office=self.province_1, location_code="W11"
        )

        self.fixed_cat = Category.objects.create(name="Laptop", is_consumable=False)
        self.cons_cat = Category.objects.create(name="Toner", is_consumable=True)

        self.provincial_user = User.objects.create_user(
            username="prov1", password="pass12345", role=UserRoles.PROVINCIAL_ADMIN, office=self.province_1
        )
        self.finance_user = User.objects.create_user(
            username="finance1", password="pass12345", role=UserRoles.FINANCE, office=self.central
        )
        self.ward_user = User.objects.create_user(
            username="ward11", password="pass12345", role=UserRoles.WARD_OFFICER, office=self.ward_11
        )

        InventoryItem.objects.create(
            category=self.fixed_cat,
            office=self.ward_11,
            title="Laptop P1",
            item_number="P1-ITM",
            item_type=InventoryItemType.FIXED_ASSET,
        )
        InventoryItem.objects.create(
            category=self.fixed_cat,
            office=self.province_2,
            title="Laptop P2",
            item_number="P2-ITM",
            item_type=InventoryItemType.FIXED_ASSET,
        )

    def test_provincial_user_sees_only_own_branch_items(self):
        self.client.force_authenticate(user=self.provincial_user)
        response = self.client.get("/api/inventory-items/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [item["title"] for item in response.data["results"]]
        self.assertIn("Laptop P1", titles)
        self.assertNotIn("Laptop P2", titles)

    def test_finance_role_is_read_only(self):
        self.client.force_authenticate(user=self.finance_user)
        payload = {
            "category": self.fixed_cat.id,
            "office": self.central.id,
            "title": "Blocked Item",
            "item_number": "FIN-1",
            "item_type": "FIXED_ASSET",
            "status": "ACTIVE",
        }
        response = self.client.post("/api/inventory-items/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ward_role_cannot_create_inventory_item(self):
        self.client.force_authenticate(user=self.ward_user)
        payload = {
            "category": self.fixed_cat.id,
            "office": self.ward_11.id,
            "title": "Ward Created Item",
            "item_number": "WARD-1",
            "item_type": "FIXED_ASSET",
            "status": "ACTIVE",
        }
        response = self.client.post("/api/inventory-items/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_stock_transaction_updates_balance(self):
        self.client.force_authenticate(user=self.provincial_user)
        item = InventoryItem.objects.create(
            category=self.cons_cat,
            office=self.ward_11,
            title="Toner A",
            item_number="CON-1",
            item_type=InventoryItemType.CONSUMABLE,
        )
        stock = ConsumableStock.objects.create(item=item, initial_quantity=50, quantity=50, min_threshold=10, unit="pcs")
        tx_payload = {
            "stock": stock.id,
            "transaction_type": "STOCK_OUT",
            "quantity": "5",
            "status": "ON_BOARDED",
            "amount": "5",
            "department": "Stores",
            "description": "Issue",
        }
        response = self.client.post("/api/consumable-stock-transactions/", tx_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        stock.refresh_from_db()
        self.assertEqual(float(stock.quantity), 45.0)

    def test_inventory_bulk_import_creates_audit_logs(self):
        self.client.force_authenticate(user=self.provincial_user)
        csv_content = (
            "title,item_number,item_type,status,category,office,amount,price,currency,store,project,department,manufacturer,description\n"
            f"Laptop B,P1-NEW,FIXED_ASSET,ACTIVE,{self.fixed_cat.id},{self.ward_11.id},0,0,,Main,PRJ,IT,Dell,Imported row\n"
        ).encode("utf-8")
        upload = SimpleUploadedFile("items.csv", csv_content, content_type="text/csv")
        response = self.client.post("/api/inventory-items/bulk-import/", {"file": upload}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 1)
        self.assertEqual(
            InventoryAuditLog.objects.filter(action_type=InventoryActionType.CREATE, remarks__icontains="bulk import").count(),
            1,
        )

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `inventory/admin.py`
```python
from django.contrib import admin


from .models import ConsumableStock, ConsumableStockTransaction, FixedAsset, InventoryItem


admin.site.register(InventoryItem)
admin.site.register(FixedAsset)
admin.site.register(ConsumableStock)
admin.site.register(ConsumableStockTransaction)

    
# Register your models here.

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `inventory/apps.py`
```python
from django.apps import AppConfig


class InventoryConfig(AppConfig):
    name = 'inventory'

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `inventory/migrations/0001_initial.py`
```python
# Generated by Django 6.0.2 on 2026-02-24 09:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('catalog', '0001_initial'),
        ('hierarchy', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InventoryItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive'), ('DISPOSED', 'Disposed')], default='ACTIVE', max_length=16)),
                ('dynamic_data', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='items', to='catalog.category')),
                ('office', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='items', to='hierarchy.office')),
            ],
        ),
        migrations.CreateModel(
            name='FixedAsset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asset_tag', models.CharField(blank=True, max_length=64)),
                ('purchase_date', models.DateField(blank=True, null=True)),
                ('item', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='fixed_asset', to='inventory.inventoryitem')),
            ],
        ),
        migrations.CreateModel(
            name='ConsumableStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('unit', models.CharField(default='pcs', max_length=32)),
                ('item', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='consumable_stock', to='inventory.inventoryitem')),
            ],
        ),
        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['category', 'office'], name='inventory_i_categor_4f399c_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['status'], name='inventory_i_status_77888d_idx'),
        ),
    ]

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `inventory/migrations/0002_consumablestock_initial_quantity_and_more.py`
```python
# Generated by Django 6.0.2 on 2026-02-25 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='consumablestock',
            name='initial_quantity',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='consumablestock',
            name='min_threshold',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='consumablestock',
            name='reorder_alert_enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='fixedasset',
            name='invoice_file',
            field=models.FileField(blank=True, null=True, upload_to='inventory/invoices/'),
        ),
        migrations.AddField(
            model_name='fixedasset',
            name='serial_number',
            field=models.CharField(blank=True, max_length=128, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='fixedasset',
            name='warranty_expiry_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `inventory/migrations/0003_consumablestocktransaction_inventoryitem_amount_and_more.py`
```python
# Generated by Django 6.0.2 on 2026-02-25 16:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_customfielddefinition_is_unique_and_more'),
        ('hierarchy', '0002_alter_office_level'),
        ('inventory', '0002_consumablestock_initial_quantity_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ConsumableStockTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('STOCK_IN', 'Stock In'), ('STOCK_OUT', 'Stock Out'), ('DAMAGE', 'Damage'), ('ADJUSTMENT', 'Adjustment')], max_length=16)),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=12)),
                ('balance_after', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('status', models.CharField(blank=True, max_length=32)),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('department', models.CharField(blank=True, max_length=128)),
                ('description', models.TextField(blank=True)),
                ('image', models.FileField(blank=True, null=True, upload_to='inventory/stock_transactions/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='currency',
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='department',
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='image',
            field=models.FileField(blank=True, null=True, upload_to='inventory/images/'),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='item_number',
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='item_type',
            field=models.CharField(choices=[('FIXED_ASSET', 'Fixed Asset'), ('CONSUMABLE', 'Consumable')], default='FIXED_ASSET', max_length=16),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='manufacturer',
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='pi_document',
            field=models.FileField(blank=True, null=True, upload_to='inventory/pi_documents/'),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='project',
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='purchased_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='store',
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='warranty_document',
            field=models.FileField(blank=True, null=True, upload_to='inventory/warranty_documents/'),
        ),
        migrations.AlterField(
            model_name='inventoryitem',
            name='status',
            field=models.CharField(choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive'), ('DISPOSED', 'Disposed'), ('ASSIGNED', 'Assigned'), ('UNASSIGNED', 'Unassigned')], default='ACTIVE', max_length=16),
        ),
        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['item_number'], name='inventory_i_item_nu_01b1d8_idx'),
        ),
        migrations.AddField(
            model_name='consumablestocktransaction',
            name='assigned_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stock_transactions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='consumablestocktransaction',
            name='performed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='performed_stock_transactions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='consumablestocktransaction',
            name='stock',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='inventory.consumablestock'),
        ),
        migrations.AddIndex(
            model_name='consumablestocktransaction',
            index=models.Index(fields=['stock', 'created_at'], name='inventory_c_stock_i_db0f9d_idx'),
        ),
        migrations.AddIndex(
            model_name='consumablestocktransaction',
            index=models.Index(fields=['transaction_type'], name='inventory_c_transac_01d5ff_idx'),
        ),
    ]

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
- `inventory/models.py`
- `inventory/serializers.py`
- `inventory/views.py`
- `inventory/urls.py`
- `inventory/tests.py`
- `inventory/admin.py`
- `inventory/apps.py`
- `inventory/migrations/0001_initial.py`
- `inventory/migrations/0002_consumablestock_initial_quantity_and_more.py`
- `inventory/migrations/0003_consumablestocktransaction_inventoryitem_amount_and_more.py`

