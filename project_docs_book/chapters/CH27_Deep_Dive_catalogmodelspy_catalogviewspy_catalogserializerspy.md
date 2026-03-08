# Chapter 27 — Deep Dive: `catalog/models.py`, `catalog/views.py`, `catalog/serializers.py`

## Build Roadmap Position
- Stage: Deep Dive
- You are here: Chapter 27
- Before this: Chapter 26
- After this: Chapter 28

## Learning Objectives
- Understand category and dynamic custom-field metadata design.
- `catalog/models.py`
- `catalog/serializers.py`

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 27 — Deep Dive: `catalog/models.py`, `catalog/views.py`, `catalog/serializers.py`

## Learning Goals
- Understand category and dynamic custom-field metadata design.

## Reference Files
- `catalog/models.py`
- `catalog/serializers.py`
- `catalog/views.py`

## Deep Dive Walkthrough

## 1) Data model
- `Category`: unique `name`, `is_consumable` flag.
- `CustomFieldType` includes `TEXT`, `NUMBER`, `DATE`, `BOOLEAN`, `SELECT`, `FILE`.
- `CustomFieldDefinition` links to category and stores field metadata:
  - `label`, `field_type`, `required`, `is_unique`, `select_options`.
- Constraints/indexes:
  - unique per `(category, label)`,
  - index on `(category, field_type)`.

## 2) Serializers
- `CategorySerializer` exposes id/name/is_consumable.
- `CustomFieldDefinitionSerializer` exposes full metadata fields.

## 3) Views
- `CategoryViewSet` and `CustomFieldDefinitionViewSet` with filter/search/order.
- Permission via `IMSAccessPermission`.
- No additional custom business method in current viewsets.

## 4) Behavior check from tests
- `catalog/tests.py` confirms central admin can create categories, provincial admin cannot.

## Chapter 27 Outcome
You now understand how catalog metadata drives flexible item attributes while keeping category-level constraints explicit.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
### File: `catalog/models.py`
```python

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_consumable = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name


class CustomFieldType(models.TextChoices):
    TEXT = "TEXT", "Text"
    NUMBER = "NUMBER", "Number"
    DATE = "DATE", "Date"
    BOOLEAN = "BOOLEAN", "Boolean"
    SELECT = "SELECT", "Select"
    FILE = "FILE", "File"


class CustomFieldDefinition(models.Model):
    category = models.ForeignKey(
        Category,
        related_name="custom_fields",
        on_delete=models.CASCADE,
    )
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=16, choices=CustomFieldType.choices)
    required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    select_options = models.JSONField(default=list, blank=True)

    class Meta:
        # "unique" per category is usually what you want:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "label"],
                name="uniq_custom_field_label_per_category",
            )
        ]
        indexes = [
            models.Index(fields=["category", "field_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.category.name}: {self.label}"

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `catalog/serializers.py`
```python
from rest_framework import serializers

from .models import Category, CustomFieldDefinition


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "is_consumable"]
        read_only_fields = ["id"]


class CustomFieldDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomFieldDefinition
        fields = [
            "id",
            "category",
            "label",
            "field_type",
            "required",
            "is_unique",
            "select_options",
        ]
        read_only_fields = ["id"]

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `catalog/views.py`
```python
from rest_framework import viewsets

from common.permissions import IMSAccessPermission
from .models import Category, CustomFieldDefinition
from .serializers import CategorySerializer, CustomFieldDefinitionSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    filterset_fields = ["is_consumable"]
    search_fields = ["name"]
    ordering_fields = ["id", "name"]
    ordering = ["id"]
    permission_classes = [IMSAccessPermission]


class CustomFieldDefinitionViewSet(viewsets.ModelViewSet):
    queryset = CustomFieldDefinition.objects.select_related("category").all().order_by("id")
    serializer_class = CustomFieldDefinitionSerializer
    filterset_fields = ["category", "field_type", "required", "is_unique"]
    search_fields = ["label", "category__name"]
    ordering_fields = ["id", "label"]
    ordering = ["id"]
    permission_classes = [IMSAccessPermission]

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
- `catalog/models.py`
- `catalog/serializers.py`
- `catalog/views.py`

