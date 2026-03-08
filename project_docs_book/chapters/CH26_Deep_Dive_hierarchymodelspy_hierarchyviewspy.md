# Chapter 26 — Deep Dive: `hierarchy/models.py`, `hierarchy/views.py`

## Build Roadmap Position
- Stage: Deep Dive
- You are here: Chapter 26
- Before this: Chapter 25
- After this: Chapter 27

## Learning Objectives
- Understand office tree modeling and how hierarchy drives API visibility.
- `hierarchy/models.py`
- `hierarchy/views.py`

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 26 — Deep Dive: `hierarchy/models.py`, `hierarchy/views.py`

## Learning Goals
- Understand office tree modeling and how hierarchy drives API visibility.

## Reference Files
- `hierarchy/models.py`
- `hierarchy/views.py`

## Deep Dive Walkthrough

## 1) Office model
- `OfficeLevels`: `CENTRAL`, `PROVINCIAL`, `LOCAL`, `WARD`.
- `Office` fields:
  - `name`, `level`, `location_code` (unique),
  - `parent_office` self-FK (`PROTECT`) for tree structure.
- Indexes: `level`, `location_code`.

## 2) View behavior
- `OfficeViewSet` is full CRUD.
- Uses `IMSAccessPermission` for role-based write restrictions.
- Uses office scoping on `id`:
  - `scope_queryset_by_user(queryset, user, "id")`.
- Supports filter/search/order configuration.

## 3) Practical effect
- Central/global roles can inspect broad hierarchy.
- Scoped roles see only accessible nodes from their assigned office subtree.

## Chapter 26 Outcome
You can now explain the office-tree data model and how it directly controls data-access boundaries across the system.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
### File: `hierarchy/models.py`
```python
from django.db import models

# Create your models here.
class OfficeLevels(models.TextChoices):
    CENTRAL ="CENTRAL","central"
    PROVINCIAL = "PROVINCIAL","provincial"
    LOCAL = "LOCAL", "local"
    WARD  = "WARD", "ward"


class Office(models.Model):
    name = models.CharField(max_length=255)
    level = models.CharField(max_length=16, choices=OfficeLevels.choices)
    parent_office = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.PROTECT,
    )
    location_code = models.CharField(max_length=64, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["level"]),
            models.Index(fields=["location_code"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.level})"

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `hierarchy/views.py`
```python
from rest_framework import viewsets

from common.access import scope_queryset_by_user
from common.permissions import IMSAccessPermission
from .models import Office
from .serializers import OfficeSerializer


class OfficeViewSet(viewsets.ModelViewSet):
    queryset = Office.objects.select_related("parent_office").all().order_by("id")
    serializer_class = OfficeSerializer
    filterset_fields = ["level", "parent_office"]
    search_fields = ["name", "location_code"]
    ordering_fields = ["id", "name", "location_code"]
    ordering = ["id"]
    permission_classes = [IMSAccessPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        return scope_queryset_by_user(queryset, self.request.user, "id")

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
- `hierarchy/models.py`
- `hierarchy/views.py`

