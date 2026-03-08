# Chapter 7 — Request Lifecycle

## Build Roadmap Position
- Stage: Execution Flow
- You are here: Chapter 7
- Before this: Chapter 6
- After this: Chapter 8

## Learning Objectives
- Understand end-to-end API request processing in this backend.
- Identify where auth, permissions, scoping, validation, persistence, and side effects occur.
- Distinguish write lifecycle and read lifecycle behavior.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 7 — Request Lifecycle

## Learning Goals
- Understand end-to-end API request processing in this backend.
- Identify where auth, permissions, scoping, validation, persistence, and side effects occur.
- Distinguish write lifecycle and read lifecycle behavior.

## Reference Files
- `django_project/urls.py`
- `common/middleware.py`
- `common/permissions.py`
- `common/access.py`
- `inventory/views.py`
- `inventory/serializers.py`
- `inventory/models.py`
- `audit/utils.py`

## Lifecycle Overview
A request in this project generally passes through:
1. URL routing
2. Middleware
3. Authentication and permission checks
4. Viewset action selection
5. Queryset scoping (for read/list/retrieve operations)
6. Serializer validation
7. Model/database write or read
8. Side effects (audit log, email, etc., where implemented)
9. Response serialization
10. Response middleware headers

## Concrete Write Flow Example: `POST /api/inventory-items/`
### 1. Route resolution
- Root URL config includes `inventory.urls` under `/api/` and `/api/v1/`.
- DRF router resolves to `InventoryItemViewSet.create`.

### 2. Middleware phase
- Request passes middleware stack.
- `LegacyApiDeprecationMiddleware` later adds deprecation headers if path starts with `/api/` and is not `/api/v1/`.

### 3. Authentication and permissions
- Global DRF defaults require authenticated user (JWT auth configured in settings).
- `InventoryItemViewSet.permission_classes = [IMSAccessPermission]`.
- `IMSAccessPermission` checks role matrix for `inventory-item` writes.

### 4. Serializer validation
- `InventoryItemSerializer.validate` enforces category-type consistency:
  - consumable category requires `CONSUMABLE` item type,
  - non-consumable category requires `FIXED_ASSET` item type.

### 5. Persistence
- Valid data is saved to `InventoryItem` model.

### 6. Post-save side effect
- `perform_create` in viewset calls `create_inventory_audit_log(...)` with action type `CREATE` and item snapshot.

### 7. Response
- DRF returns created resource payload (standard `ModelViewSet.create` behavior).
- Legacy `/api/*` requests receive deprecation metadata headers from middleware.

## Concrete Read Flow Example: `GET /api/inventory-items/`
### 1. Route and middleware
- Same routing and middleware entry behavior.

### 2. Authentication and permissions
- Safe method (`GET`) passes permission check for users with a role.

### 3. Queryset scoping
- `get_queryset` calls `scope_queryset_by_user(queryset, request.user, "office_id")`.
- Returned rows depend on user role and accessible offices.

### 4. Filtering/search/ordering/pagination
- DRF applies filter/search/ordering backends configured globally plus viewset fields.
- Paginated response is returned (page-number pagination).

## Lifecycle With Transactional Domain Mutation Example
For `POST /api/consumable-stock-transactions/`:
- serializer `create` runs inside `@transaction.atomic`.
- stock quantity is adjusted and `balance_after` is computed.
- insufficient stock raises validation error.
- `perform_create` sets `performed_by`, writes audit log, and may send low-stock alert email if threshold is crossed and recipients are configured.

## Where Core Lifecycle Responsibilities Live
- Routing: `django_project/urls.py` + app routers
- Middleware response metadata: `common/middleware.py`
- Permission gate: `common/permissions.py`
- Data scope gate: `common/access.py`
- Request handling and side effects: app `views.py`
- Validation and some transactional business logic: app `serializers.py`
- Storage constraints: app `models.py`

## Error/Failure Points in Lifecycle
- Authentication failure -> 401/403 path via DRF/auth permission flow.
- Role permission failure -> 403 from `IMSAccessPermission`.
- Serializer validation failure -> 400 with field errors.
- Transactional stock rule failure -> 400 (insufficient quantity).

## Chapter 7 Outcome
You now have a practical request lifecycle map from inbound URL to final response, including where this codebase enforces security, business rules, data visibility, persistence, and side effects.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
### File: `django_project/urls.py`
```python
from django.contrib import admin
from django.conf import settings
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", lambda request: JsonResponse({"status": "ok"}), name="health"),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="v1-token-obtain-pair"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="v1-token-refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="v1-schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="v1-schema"), name="v1-swagger-ui"),
    path("api/", include("users.urls")),
    path("api/", include("hierarchy.urls")),
    path("api/", include("catalog.urls")),
    path("api/", include("inventory.urls")),
    path("api/", include("actions.urls")),
    path("api/", include("audit.urls")),
    path("api/", include("reports.urls")),
    path("api/v1/", include("users.urls")),
    path("api/v1/", include("hierarchy.urls")),
    path("api/v1/", include("catalog.urls")),
    path("api/v1/", include("inventory.urls")),
    path("api/v1/", include("actions.urls")),
    path("api/v1/", include("audit.urls")),
    path("api/v1/", include("reports.urls")),
]

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `common/middleware.py`
```python
class LegacyApiDeprecationMiddleware:
    """
    Adds RFC-style deprecation metadata for legacy /api/* routes while /api/v1/* is active.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path or ""
        if path.startswith("/api/") and not path.startswith("/api/v1/"):
            response["Deprecation"] = "true"
            response["Sunset"] = "Wed, 31 Dec 2026 23:59:59 GMT"
            response["Link"] = '</api/v1/>; rel="successor-version"'
        return response

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `common/permissions.py`
```python
from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.models import UserRoles


READ_ONLY_ROLES = {
    UserRoles.FINANCE,
    UserRoles.AUDIT,
}

WRITE_ROLES = {
    UserRoles.SUPER_ADMIN,
    UserRoles.CENTRAL_ADMIN,
    UserRoles.CENTRAL_PROCUREMENT_STORE,
    UserRoles.PROVINCIAL_ADMIN,
    UserRoles.LOCAL_ADMIN,
    UserRoles.WARD_OFFICER,
}

WRITE_ROLE_MATRIX = {
    "office": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
    },
    "category": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
    },
    "custom-field-definition": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
    },
    "inventory-item": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
        UserRoles.CENTRAL_PROCUREMENT_STORE,
        UserRoles.PROVINCIAL_ADMIN,
        UserRoles.LOCAL_ADMIN,
    },
    "fixed-asset": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
        UserRoles.CENTRAL_PROCUREMENT_STORE,
        UserRoles.PROVINCIAL_ADMIN,
        UserRoles.LOCAL_ADMIN,
    },
    "consumable-stock": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
        UserRoles.CENTRAL_PROCUREMENT_STORE,
        UserRoles.PROVINCIAL_ADMIN,
        UserRoles.LOCAL_ADMIN,
    },
    "consumable-stock-transaction": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
        UserRoles.CENTRAL_PROCUREMENT_STORE,
        UserRoles.PROVINCIAL_ADMIN,
        UserRoles.LOCAL_ADMIN,
        UserRoles.WARD_OFFICER,
    },
    "item-assignment": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
        UserRoles.CENTRAL_PROCUREMENT_STORE,
        UserRoles.PROVINCIAL_ADMIN,
        UserRoles.LOCAL_ADMIN,
    },
    "inventory-audit-log": set(),
}


class IMSAccessPermission(BasePermission):
    """
    Role baseline from PRD:
    - Finance/Audit: read-only
    - Operational/admin roles: read-write
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_staff or user.is_superuser:
            return True

        if request.method in SAFE_METHODS:
            return bool(user.role)

        if user.role in READ_ONLY_ROLES:
            return False

        view_basename = getattr(view, "basename", None)
        if view_basename in WRITE_ROLE_MATRIX:
            return user.role in WRITE_ROLE_MATRIX[view_basename]

        return user.role in WRITE_ROLES

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

## Rebuild Step (Hands-on Roadmap)
- Implement or review the files listed in this chapter only.
- Validate behavior discussed in the original chapter explanation.
- Confirm readiness for the next chapter transition.

## Chapter Summary
This chapter ties repository explanation to exact code references and prepares the next build step.

## Files Used
- `django_project/urls.py`
- `common/middleware.py`
- `common/permissions.py`
- `common/access.py`
- `inventory/views.py`
- `inventory/serializers.py`
- `inventory/models.py`
- `audit/utils.py`

