# Chapter 31 — Deep Dive: `actions/models.py`, `actions/serializers.py`, `actions/views.py`

## Build Roadmap Position
- Stage: Deep Dive
- You are here: Chapter 31
- Before this: Chapter 30
- After this: Chapter 32

## Learning Objectives
- Understand assignment lifecycle rules and API hooks.
- `actions/models.py`
- `actions/serializers.py`

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 31 — Deep Dive: `actions/models.py`, `actions/serializers.py`, `actions/views.py`

## Learning Goals
- Understand assignment lifecycle rules and API hooks.

## Reference Files
- `actions/models.py`
- `actions/serializers.py`
- `actions/views.py`

## Deep Dive Walkthrough

## 1) Model constraints
- `ItemAssignment` requires at least one target (`assigned_to_user` or `assigned_to_office`).
- Enforces one active assignment per item using conditional unique constraint on `status=ASSIGNED`.
- Requires `returned_at` when status is `RETURNED`.

## 2) Serializer checks
- `ItemAssignmentSerializer.validate` mirrors model business rules.
- Exposes `item_name` and `item_number` read-only fields.

## 3) Viewset lifecycle
- Queryset is office-scoped and permission-protected.
- `perform_create` sets `assigned_by` and writes `ASSIGN` audit log.
- `perform_update` compares before/after state and writes `ASSIGN` or `RETURN` audit event.

## 4) Custom actions
- `summary_by_assignee`: grouped totals with `active`, `overdue`, `returned` metrics.
- `bulk_import`: CSV-driven assignment creation with per-row validation + audit logs.

## Chapter 31 Outcome
You can now explain assignment workflow integrity from database constraints to API-level audit side effects.
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

