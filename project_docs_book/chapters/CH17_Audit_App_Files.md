# Chapter 17 — Audit App Files

## Build Roadmap Position
- Stage: Core Domain
- You are here: Chapter 17
- Before this: Chapter 16
- After this: Chapter 18

## Learning Objectives
- Understand how inventory actions are captured as immutable audit records.
- Trace audit read APIs, serializer shape, and helper utilities.
- Verify read-only behavior from tests.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 17 — Audit App Files

## Learning Goals
- Understand how inventory actions are captured as immutable audit records.
- Trace audit read APIs, serializer shape, and helper utilities.
- Verify read-only behavior from tests.

## Reference Files
- `audit/models.py`
- `audit/serializers.py`
- `audit/views.py`
- `audit/urls.py`
- `audit/utils.py`
- `audit/tests.py`
- `audit/admin.py`
- `audit/apps.py`
- `audit/migrations/0001_initial.py`

## File Breakdown

## 1) `audit/models.py`
- `InventoryActionType` enum: `CREATE`, `UPDATE`, `ASSIGN`, `RETURN`, `REPAIR`, `DISPOSE`.
- `InventoryAuditLog` stores:
  - target item (`item` FK), actor (`performed_by` FK), action type,
  - `before_data` / `after_data` JSON snapshots,
  - `remarks`, optional `attachment`, `created_at`.
- Indexes exist on `(item, created_at)` and `action_type`.

## 2) `audit/serializers.py`
- `InventoryAuditLogSerializer` adds display fields:
  - `item_name`, `item_number`, `performed_by_name`.
- Core model fields are exposed, with read-only `id`, `performed_by`, `created_at`.

## 3) `audit/views.py`
- `InventoryAuditLogViewSet` is `ReadOnlyModelViewSet`.
- Includes filter/search/order settings.
- Queryset is office-scoped via:
  - `scope_queryset_by_user(queryset, request.user, "item__office_id")`.
- Permission class: `IMSAccessPermission`.

## 4) `audit/utils.py`
- `create_inventory_audit_log(...)` centralizes log creation.
- `item_snapshot(item)` returns a normalized item dictionary used by other apps.

## 5) `audit/urls.py`
- Router registers `audit-logs` endpoint.
- Available under `/api/audit-logs/` and `/api/v1/audit-logs/`.

## 6) `audit/tests.py`
- `AuditLogReadOnlyTests` verifies:
  - GET list is allowed (`200`).
  - POST create is blocked (`403`).

## 7) Other files
- `audit/admin.py` registers `InventoryAuditLog`.
- `audit/apps.py` defines `AuditConfig`.
- Migration `0001_initial.py` creates the audit table and indexes.

## Chapter 17 Outcome
You now have a complete map of the audit subsystem: schema, serializer output, read API behavior, helper functions, and enforcement of read-only access.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
### File: `audit/models.py`
```python
from django.conf import settings
from django.db import models

from inventory.models import InventoryItem


class InventoryActionType(models.TextChoices):
    CREATE = "CREATE", "Create"
    UPDATE = "UPDATE", "Update"
    ASSIGN = "ASSIGN", "Assign"
    RETURN = "RETURN", "Return"
    REPAIR = "REPAIR", "Repair"
    DISPOSE = "DISPOSE", "Dispose"


class InventoryAuditLog(models.Model):
    item = models.ForeignKey(InventoryItem, related_name="audit_logs", on_delete=models.CASCADE)
    action_type = models.CharField(max_length=16, choices=InventoryActionType.choices)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="inventory_audit_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    before_data = models.JSONField(default=dict, blank=True)
    after_data = models.JSONField(default=dict, blank=True)
    remarks = models.TextField(blank=True)
    attachment = models.FileField(upload_to="inventory/audit_attachments/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["item", "created_at"]),
            models.Index(fields=["action_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.item.title} - {self.action_type}"

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `audit/serializers.py`
```python
from rest_framework import serializers

from .models import InventoryAuditLog


class InventoryAuditLogSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.title", read_only=True)
    item_number = serializers.CharField(source="item.item_number", read_only=True)
    performed_by_name = serializers.SerializerMethodField()

    def get_performed_by_name(self, obj):
        if not obj.performed_by:
            return None
        return obj.performed_by.get_full_name() or obj.performed_by.username

    class Meta:
        model = InventoryAuditLog
        fields = [
            "id",
            "item",
            "item_name",
            "item_number",
            "action_type",
            "performed_by",
            "performed_by_name",
            "before_data",
            "after_data",
            "remarks",
            "attachment",
            "created_at",
        ]
        read_only_fields = ["id", "performed_by", "created_at"]

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `audit/views.py`
```python
from rest_framework import viewsets

from common.access import scope_queryset_by_user
from common.permissions import IMSAccessPermission
from .models import InventoryAuditLog
from .serializers import InventoryAuditLogSerializer


class InventoryAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventoryAuditLog.objects.select_related("item", "performed_by").all().order_by("id")
    serializer_class = InventoryAuditLogSerializer
    filterset_fields = ["item", "action_type", "performed_by"]
    search_fields = ["item__title", "remarks", "performed_by__username"]
    ordering_fields = ["id", "created_at"]
    ordering = ["-created_at"]
    permission_classes = [IMSAccessPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        return scope_queryset_by_user(queryset, self.request.user, "item__office_id")

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `audit/urls.py`
```python
from rest_framework.routers import DefaultRouter

from .views import InventoryAuditLogViewSet

router = DefaultRouter()
router.register(r"audit-logs", InventoryAuditLogViewSet, basename="inventory-audit-log")

urlpatterns = router.urls

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

### File: `audit/tests.py`
```python
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category
from hierarchy.models import Office, OfficeLevels
from inventory.models import InventoryItem, InventoryItemType
from users.models import User, UserRoles

from .models import InventoryActionType, InventoryAuditLog


class AuditLogReadOnlyTests(APITestCase):
    def setUp(self):
        self.central = Office.objects.create(name="Central", level=OfficeLevels.CENTRAL, location_code="CENTRAL-1")
        self.category = Category.objects.create(name="Printer", is_consumable=False)
        self.user = User.objects.create_user(
            username="central_admin",
            password="pass12345",
            role=UserRoles.CENTRAL_ADMIN,
            office=self.central,
        )
        self.item = InventoryItem.objects.create(
            category=self.category,
            office=self.central,
            title="Printer A",
            item_number="PRN-1",
            item_type=InventoryItemType.FIXED_ASSET,
        )
        InventoryAuditLog.objects.create(
            item=self.item,
            action_type=InventoryActionType.CREATE,
            performed_by=self.user,
            remarks="Seed log",
        )
        self.client.force_authenticate(user=self.user)

    def test_read_is_allowed(self):
        response = self.client.get("/api/audit-logs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_is_not_allowed(self):
        payload = {
            "item": self.item.id,
            "action_type": InventoryActionType.UPDATE,
            "remarks": "Should be blocked",
        }
        response = self.client.post("/api/audit-logs/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `audit/admin.py`
```python
from django.contrib import admin

from .models import InventoryAuditLog


admin.site.register(InventoryAuditLog)

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `audit/apps.py`
```python
from django.apps import AppConfig


class AuditConfig(AppConfig):
    name = 'audit'

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `audit/migrations/0001_initial.py`
```python
# Generated by Django 6.0.2 on 2026-02-25 07:58

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('inventory', '0002_consumablestock_initial_quantity_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='InventoryAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(choices=[('CREATE', 'Create'), ('UPDATE', 'Update'), ('ASSIGN', 'Assign'), ('RETURN', 'Return'), ('REPAIR', 'Repair'), ('DISPOSE', 'Dispose')], max_length=16)),
                ('before_data', models.JSONField(blank=True, default=dict)),
                ('after_data', models.JSONField(blank=True, default=dict)),
                ('remarks', models.TextField(blank=True)),
                ('attachment', models.FileField(blank=True, null=True, upload_to='inventory/audit_attachments/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='inventory.inventoryitem')),
                ('performed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inventory_audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['item', 'created_at'], name='audit_inven_item_id_450cff_idx'), models.Index(fields=['action_type'], name='audit_inven_action__f63087_idx')],
            },
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
- `audit/models.py`
- `audit/serializers.py`
- `audit/views.py`
- `audit/urls.py`
- `audit/utils.py`
- `audit/tests.py`
- `audit/admin.py`
- `audit/apps.py`
- `audit/migrations/0001_initial.py`

