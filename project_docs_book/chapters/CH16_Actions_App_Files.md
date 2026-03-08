# Chapter 16 — Actions App Files

## Build Roadmap Position
- Stage: Core Domain
- You are here: Chapter 16
- Before this: Chapter 15
- After this: Chapter 17

## Learning Objectives
- Understand the assignment workflow model and constraints.
- Learn assignment API behavior for create/update/summary/bulk import.
- Map audit coupling and migration history for actions.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 16 — Actions App Files

## Learning Goals
- Understand the assignment workflow model and constraints.
- Learn assignment API behavior for create/update/summary/bulk import.
- Map audit coupling and migration history for actions.

## Reference Files
- `actions/models.py`
- `actions/serializers.py`
- `actions/views.py`
- `actions/urls.py`
- `actions/tests.py`
- `actions/admin.py`
- `actions/apps.py`
- `actions/migrations/0001_initial.py`
- `actions/migrations/0002_itemassignment_assign_till.py`

## File Breakdown

## 1) `actions/models.py`
### Enums
- `AssignmentStatus`: `ASSIGNED`, `RETURNED`
- `ItemCondition`: `GOOD`, `FAIR`, `DAMAGED`

### `ItemAssignment`
Core fields:
- target item (`item` FK to inventory)
- assignment target (`assigned_to_user` and/or `assigned_to_office`)
- assignment actor (`assigned_by`)
- lifecycle fields (`handover_date`, `assign_till`, `status`, `returned_at`)
- condition/evidence fields (`handover_condition`, `return_condition`, `handover_letter`, `damage_photo`)
- `remarks`, `created_at`

Constraints:
- check constraint: at least one assignment target is required.
- unique constraint: only one active (`ASSIGNED`) assignment per item.
- indexes on `status` and `handover_date`.

Model clean rules:
- reject missing assignment target.
- reject `RETURNED` status without `returned_at`.

## 2) `actions/serializers.py`
### `ItemAssignmentSerializer`
- Adds read-only convenience fields:
  - `item_name`
  - `item_number`
- Validation mirrors model rules:
  - requires assignment target
  - requires `returned_at` when status is `RETURNED`
- `assigned_by` is read-only from API perspective.

## 3) `actions/views.py`
### `ItemAssignmentViewSet`
- CRUD with filter/search/ordering.
- Permission: `IMSAccessPermission`.
- Queryset scoping via `scope_queryset_by_user(..., "item__office_id")`.

Write hooks:
- `perform_create`:
  - sets `assigned_by` from request user,
  - creates audit log with `ASSIGN` action.
- `perform_update`:
  - captures before snapshot,
  - chooses audit action (`RETURN` when status becomes returned, else `ASSIGN`),
  - writes before/after audit data.

Custom actions:
- `summary_by_assignee` (GET):
  - grouped aggregate counts (`total_items`, `active`, `overdue`, `returned`).
- `bulk_import` (POST CSV):
  - row-wise validation/save,
  - audit logging for successful rows,
  - returns created/failed summary and error details.

## 4) `actions/urls.py`
- Router registers `ItemAssignmentViewSet` at `item-assignments`.
- Effective paths:
  - `/api/item-assignments/`
  - `/api/v1/item-assignments/`
  - plus custom action paths (`summary-by-assignee`, `bulk-import`).

## 5) `actions/tests.py`
`AssignmentRoleMatrixTests` validates:
- local admin can create assignment (`201`).
- ward user cannot create assignment (`403`).
- bulk import creates assignment plus corresponding audit records.

## 6) `actions/admin.py`
- Registers `ItemAssignment` for admin management.

## 7) `actions/apps.py`
- Declares app config `ActionsConfig` with `name='actions'`.

## 8) Migration Evolution
- `0001_initial.py`:
  - introduces `ItemAssignment` table with constraints/indexes and full core fields.
- `0002_itemassignment_assign_till.py`:
  - adds optional `assign_till` date field.

## Actions App Responsibilities (Observed)
- manages assignment and return workflow for inventory items.
- enforces one-active-assignment rule per item.
- provides assignment reporting endpoint (`summary-by-assignee`).
- generates audit events for assignment lifecycle changes.

## Architecture Notes
- Actions is tightly coupled to inventory (item target) and audit (event logging).
- Assignment visibility is office-scoped through shared access module.
- Workflow constraints are enforced redundantly across model and serializer layers.

## Chapter 16 Outcome
You now have a full map of the actions app: assignment schema, API lifecycle behavior, audit coupling, reporting action, and migration-based evolution.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
### File: `actions/models.py`
```python
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from hierarchy.models import Office
from inventory.models import InventoryItem


class AssignmentStatus(models.TextChoices):
    ASSIGNED = "ASSIGNED", "Assigned"
    RETURNED = "RETURNED", "Returned"


class ItemCondition(models.TextChoices):
    GOOD = "GOOD", "Good"
    FAIR = "FAIR", "Fair"
    DAMAGED = "DAMAGED", "Damaged"


class ItemAssignment(models.Model):
    item = models.ForeignKey(InventoryItem, related_name="assignments", on_delete=models.CASCADE)
    assigned_to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="item_assignments",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    assigned_to_office = models.ForeignKey(
        Office,
        related_name="item_assignments",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="assigned_items",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    handover_date = models.DateField()
    assign_till = models.DateField(null=True, blank=True)
    handover_condition = models.CharField(max_length=16, choices=ItemCondition.choices, default=ItemCondition.GOOD)
    handover_letter = models.FileField(upload_to="inventory/handover_letters/", null=True, blank=True)
    status = models.CharField(max_length=16, choices=AssignmentStatus.choices, default=AssignmentStatus.ASSIGNED)
    returned_at = models.DateTimeField(null=True, blank=True)
    return_condition = models.CharField(max_length=16, choices=ItemCondition.choices, null=True, blank=True)
    damage_photo = models.FileField(upload_to="inventory/damage_photos/", null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(Q(assigned_to_user__isnull=False) | Q(assigned_to_office__isnull=False)),
                name="item_assignment_target_required",
            ),
            models.UniqueConstraint(
                fields=["item"],
                condition=Q(status=AssignmentStatus.ASSIGNED),
                name="uniq_active_assignment_per_item",
            ),
        ]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["handover_date"]),
        ]

    def clean(self):
        super().clean()
        if not self.assigned_to_user_id and not self.assigned_to_office_id:
            raise ValidationError("Assignment must target a user or an office.")
        if self.status == AssignmentStatus.RETURNED and not self.returned_at:
            raise ValidationError("Returned assignment must include returned_at.")

    def __str__(self) -> str:
        return f"{self.item.title} - {self.status}"

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `actions/serializers.py`
```python
from rest_framework import serializers

from .models import AssignmentStatus, ItemAssignment


class ItemAssignmentSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.title", read_only=True)
    item_number = serializers.CharField(source="item.item_number", read_only=True)

    def validate(self, attrs):
        status = attrs.get("status", getattr(self.instance, "status", None))
        returned_at = attrs.get("returned_at", getattr(self.instance, "returned_at", None))
        assigned_to_user = attrs.get("assigned_to_user", getattr(self.instance, "assigned_to_user", None))
        assigned_to_office = attrs.get("assigned_to_office", getattr(self.instance, "assigned_to_office", None))

        if not assigned_to_user and not assigned_to_office:
            raise serializers.ValidationError({"non_field_errors": ["Assignment must target a user or an office."]})
        if status == AssignmentStatus.RETURNED and not returned_at:
            raise serializers.ValidationError({"returned_at": "Returned assignment must include returned_at."})
        return attrs

    class Meta:
        model = ItemAssignment
        fields = [
            "id",
            "item",
            "assigned_to_user",
            "assigned_to_office",
            "assigned_by",
            "handover_date",
            "assign_till",
            "handover_condition",
            "handover_letter",
            "status",
            "returned_at",
            "return_condition",
            "damage_photo",
            "remarks",
            "item_name",
            "item_number",
            "created_at",
        ]
        read_only_fields = ["id", "assigned_by", "created_at"]

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

### File: `actions/urls.py`
```python
from rest_framework.routers import DefaultRouter

from .views import ItemAssignmentViewSet

router = DefaultRouter()
router.register(r"item-assignments", ItemAssignmentViewSet, basename="item-assignment")

urlpatterns = router.urls

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `actions/tests.py`
```python
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from audit.models import InventoryActionType, InventoryAuditLog
from catalog.models import Category
from hierarchy.models import Office, OfficeLevels
from inventory.models import InventoryItem, InventoryItemType
from users.models import User, UserRoles


class AssignmentRoleMatrixTests(APITestCase):
    def setUp(self):
        self.central = Office.objects.create(name="Central", level=OfficeLevels.CENTRAL, location_code="C-1")
        self.local = Office.objects.create(
            name="Local 1",
            level=OfficeLevels.LOCAL,
            parent_office=self.central,
            location_code="L-1",
        )
        self.category = Category.objects.create(name="Laptop", is_consumable=False)
        self.item = InventoryItem.objects.create(
            category=self.category,
            office=self.local,
            title="Laptop A",
            item_number="LT-001",
            item_type=InventoryItemType.FIXED_ASSET,
        )
        self.employee = User.objects.create_user(
            username="employee1",
            password="pass12345",
            role=UserRoles.WARD_OFFICER,
            office=self.local,
        )
        self.local_admin = User.objects.create_user(
            username="local_admin",
            password="pass12345",
            role=UserRoles.LOCAL_ADMIN,
            office=self.local,
        )
        self.ward_user = User.objects.create_user(
            username="ward_user",
            password="pass12345",
            role=UserRoles.WARD_OFFICER,
            office=self.local,
        )

    def _payload(self):
        return {
            "item": self.item.id,
            "assigned_to_user": self.employee.id,
            "handover_date": "2026-01-01",
            "status": "ASSIGNED",
        }

    def test_local_admin_can_create_assignment(self):
        self.client.force_authenticate(user=self.local_admin)
        response = self.client.post("/api/item-assignments/", self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_ward_user_cannot_create_assignment(self):
        self.client.force_authenticate(user=self.ward_user)
        response = self.client.post("/api/item-assignments/", self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assignment_bulk_import_creates_audit_logs(self):
        self.client.force_authenticate(user=self.local_admin)
        csv_content = (
            "item,assigned_to_user,assigned_to_office,handover_date,assign_till,handover_condition,status,remarks\n"
            f"{self.item.id},{self.employee.id},,2026-01-01,2026-12-31,GOOD,ASSIGNED,Bulk assigned\n"
        ).encode("utf-8")
        upload = SimpleUploadedFile("assignments.csv", csv_content, content_type="text/csv")
        response = self.client.post("/api/item-assignments/bulk-import/", {"file": upload}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 1)
        self.assertEqual(
            InventoryAuditLog.objects.filter(action_type=InventoryActionType.ASSIGN, remarks__icontains="bulk import").count(),
            1,
        )

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `actions/admin.py`
```python
from django.contrib import admin

from .models import ItemAssignment


admin.site.register(ItemAssignment)


```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `actions/apps.py`
```python
from django.apps import AppConfig


class ActionsConfig(AppConfig):
    name = 'actions'

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `actions/migrations/0001_initial.py`
```python
# Generated by Django 6.0.2 on 2026-02-25 07:58

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('hierarchy', '0002_alter_office_level'),
        ('inventory', '0002_consumablestock_initial_quantity_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('handover_date', models.DateField()),
                ('handover_condition', models.CharField(choices=[('GOOD', 'Good'), ('FAIR', 'Fair'), ('DAMAGED', 'Damaged')], default='GOOD', max_length=16)),
                ('handover_letter', models.FileField(blank=True, null=True, upload_to='inventory/handover_letters/')),
                ('status', models.CharField(choices=[('ASSIGNED', 'Assigned'), ('RETURNED', 'Returned')], default='ASSIGNED', max_length=16)),
                ('returned_at', models.DateTimeField(blank=True, null=True)),
                ('return_condition', models.CharField(blank=True, choices=[('GOOD', 'Good'), ('FAIR', 'Fair'), ('DAMAGED', 'Damaged')], max_length=16, null=True)),
                ('damage_photo', models.FileField(blank=True, null=True, upload_to='inventory/damage_photos/')),
                ('remarks', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assigned_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_items', to=settings.AUTH_USER_MODEL)),
                ('assigned_to_office', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='item_assignments', to='hierarchy.office')),
                ('assigned_to_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='item_assignments', to=settings.AUTH_USER_MODEL)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='inventory.inventoryitem')),
            ],
            options={
                'indexes': [models.Index(fields=['status'], name='actions_ite_status_1f17ad_idx'), models.Index(fields=['handover_date'], name='actions_ite_handove_a862d8_idx')],
                'constraints': [models.CheckConstraint(condition=models.Q(('assigned_to_user__isnull', False), ('assigned_to_office__isnull', False), _connector='OR'), name='item_assignment_target_required'), models.UniqueConstraint(condition=models.Q(('status', 'ASSIGNED')), fields=('item',), name='uniq_active_assignment_per_item')],
            },
        ),
    ]

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `actions/migrations/0002_itemassignment_assign_till.py`
```python
# Generated by Django 6.0.2 on 2026-02-25 16:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemassignment',
            name='assign_till',
            field=models.DateField(blank=True, null=True),
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
- `actions/models.py`
- `actions/serializers.py`
- `actions/views.py`
- `actions/urls.py`
- `actions/tests.py`
- `actions/admin.py`
- `actions/apps.py`
- `actions/migrations/0001_initial.py`
- `actions/migrations/0002_itemassignment_assign_till.py`

