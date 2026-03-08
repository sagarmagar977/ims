# Chapter 32 — Deep Dive: `audit/models.py`, `audit/views.py`, `audit/utils.py`

## Build Roadmap Position
- Stage: Deep Dive
- You are here: Chapter 32
- Before this: Chapter 31
- After this: Chapter 33

## Learning Objectives
- Understand audit storage schema and helper-driven event creation.
- `audit/models.py`
- `audit/views.py`

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 32 — Deep Dive: `audit/models.py`, `audit/views.py`, `audit/utils.py`

## Learning Goals
- Understand audit storage schema and helper-driven event creation.

## Reference Files
- `audit/models.py`
- `audit/views.py`
- `audit/utils.py`

## Deep Dive Walkthrough

## 1) Audit storage design
- `InventoryAuditLog` keeps structured before/after JSON and optional attachment.
- Action type is normalized through `InventoryActionType` enum.

## 2) Read API design
- `InventoryAuditLogViewSet` is read-only by class type.
- Includes filter/search/order fields for traceability use cases.
- Office scope uses `item__office_id` relation path.

## 3) Utility contract
- `create_inventory_audit_log(...)` is a centralized write helper used by inventory/actions flows.
- `item_snapshot(item)` provides consistent payload keys for audit entries.

## 4) Practical implication
- The project favors explicit event writes from business endpoints over model signals.

## Chapter 32 Outcome
You now understand the audit event contract and where/how audit records are generated and consumed.
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
- `audit/models.py`
- `audit/views.py`
- `audit/utils.py`

