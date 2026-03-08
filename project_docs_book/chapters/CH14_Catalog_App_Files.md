# Chapter 14 — Catalog App Files

## Build Roadmap Position
- Stage: Core Domain
- You are here: Chapter 14
- Before this: Chapter 13
- After this: Chapter 15

## Learning Objectives
- Understand how item categories and dynamic field definitions are modeled.
- Learn catalog API permissions and query capabilities.
- Map catalog seed and migration evolution.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 14 — Catalog App Files

## Learning Goals
- Understand how item categories and dynamic field definitions are modeled.
- Learn catalog API permissions and query capabilities.
- Map catalog seed and migration evolution.

## Reference Files
- `catalog/models.py`
- `catalog/serializers.py`
- `catalog/views.py`
- `catalog/urls.py`
- `catalog/tests.py`
- `catalog/admin.py`
- `catalog/apps.py`
- `catalog/migrations/0001_initial.py`
- `catalog/migrations/0002_customfielddefinition_is_unique_and_more.py`
- `catalog/management/commands/seed_initial_categories.py`

## File Breakdown

## 1) `catalog/models.py`
### `Category`
- Fields:
  - `name` (unique)
  - `is_consumable` (bool)
- Purpose:
  - classifies inventory domain into consumable vs fixed-asset compatible groups.

### `CustomFieldType`
- Enum of dynamic field types:
  - `TEXT`, `NUMBER`, `DATE`, `BOOLEAN`, `SELECT`, `FILE`

### `CustomFieldDefinition`
- Fields:
  - `category` FK
  - `label`
  - `field_type`
  - `required`
  - `is_unique`
  - `select_options` (JSON list)
- Constraints/Indexes:
  - unique (`category`, `label`)
  - index on (`category`, `field_type`)

Purpose:
- category-specific metadata schema for dynamic item attributes.

## 2) `catalog/serializers.py`
- `CategorySerializer` exposes `id`, `name`, `is_consumable`.
- `CustomFieldDefinitionSerializer` exposes all custom field definition attributes.
- No custom serializer validation logic beyond model constraints.

## 3) `catalog/views.py`
### `CategoryViewSet`
- `ModelViewSet` with:
  - filtering by `is_consumable`
  - search by `name`
  - ordering by `id`/`name`
- permission: `IMSAccessPermission`

### `CustomFieldDefinitionViewSet`
- `ModelViewSet` with:
  - filtering by `category`, `field_type`, `required`, `is_unique`
  - search by `label` and category name
  - ordering by `id`/`label`
- permission: `IMSAccessPermission`

## 4) `catalog/urls.py`
Router endpoints:
- `categories`
- `custom-fields`

Effective root paths:
- `/api/categories/`, `/api/custom-fields/`
- `/api/v1/categories/`, `/api/v1/custom-fields/`

## 5) `catalog/tests.py`
### `CategoryRoleMatrixTests`
- confirms central admin can create category (`201`).
- confirms provincial admin cannot create category (`403`).

This validates role matrix behavior for catalog writes.

## 6) `catalog/admin.py`
- Registers `Category` and `CustomFieldDefinition` in admin.

## 7) `catalog/apps.py`
- App config `CatalogConfig` with `name='catalog'`.

## 8) Migration Evolution
- `0001_initial.py`:
  - creates `Category` and `CustomFieldDefinition`.
  - initial custom field types included up to `SELECT`.
  - sets unique and index constraints.
- `0002_customfielddefinition_is_unique_and_more.py`:
  - adds `is_unique`.
  - adds `select_options` JSON field.
  - extends `field_type` choices to include `FILE`.

## 9) Seed Command: `seed_initial_categories.py`
- Seeds fixed-asset and consumable category sets.
- Idempotent behavior:
  - create if missing,
  - update `is_consumable` if mismatched,
  - otherwise unchanged.
- Supports `--dry-run` with transaction rollback.

## Catalog App Responsibilities (Observed)
- provides master category reference for inventory items.
- defines dynamic field schema per category.
- establishes consumable/fixed-asset classification used by inventory validation.
- offers bootstrap category dataset via management command.

## Architecture Notes
- Catalog is a dependency input for inventory business rules.
- Dynamic schema (`CustomFieldDefinition`) enables category-driven extension without hardcoding model columns.
- Write control depends on centralized role permissions from `common.permissions`.

## Chapter 14 Outcome
You now have a complete map of catalog app behavior: category taxonomy, dynamic field metadata, API controls, migration evolution, and seed automation for baseline data.
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

### File: `catalog/urls.py`
```python
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, CustomFieldDefinitionViewSet

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"custom-fields", CustomFieldDefinitionViewSet, basename="custom-field-definition")

urlpatterns = router.urls

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `catalog/tests.py`
```python
from rest_framework import status
from rest_framework.test import APITestCase

from hierarchy.models import Office, OfficeLevels
from users.models import User, UserRoles


class CategoryRoleMatrixTests(APITestCase):
    def setUp(self):
        self.central = Office.objects.create(name="Central", level=OfficeLevels.CENTRAL, location_code="CEN")
        self.province = Office.objects.create(
            name="Province 1",
            level=OfficeLevels.PROVINCIAL,
            parent_office=self.central,
            location_code="PROV-1",
        )
        self.central_admin = User.objects.create_user(
            username="central_admin",
            password="pass12345",
            role=UserRoles.CENTRAL_ADMIN,
            office=self.central,
        )
        self.provincial_admin = User.objects.create_user(
            username="prov_admin",
            password="pass12345",
            role=UserRoles.PROVINCIAL_ADMIN,
            office=self.province,
        )

    def test_central_admin_can_create_category(self):
        self.client.force_authenticate(user=self.central_admin)
        response = self.client.post("/api/categories/", {"name": "Laptop", "is_consumable": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_provincial_admin_cannot_create_category(self):
        self.client.force_authenticate(user=self.provincial_admin)
        response = self.client.post("/api/categories/", {"name": "Toner", "is_consumable": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `catalog/admin.py`
```python
from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Category)
admin.site.register(CustomFieldDefinition)



```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `catalog/apps.py`
```python
from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = 'catalog'

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `catalog/migrations/0001_initial.py`
```python
# Generated by Django 6.0.2 on 2026-02-24 08:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('is_consumable', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='CustomFieldDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=255)),
                ('field_type', models.CharField(choices=[('TEXT', 'Text'), ('NUMBER', 'Number'), ('DATE', 'Date'), ('BOOLEAN', 'Boolean'), ('SELECT', 'Select')], max_length=16)),
                ('required', models.BooleanField(default=False)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='custom_fields', to='catalog.category')),
            ],
            options={
                'indexes': [models.Index(fields=['category', 'field_type'], name='catalog_cus_categor_49b57a_idx')],
                'constraints': [models.UniqueConstraint(fields=('category', 'label'), name='uniq_custom_field_label_per_category')],
            },
        ),
    ]

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `catalog/migrations/0002_customfielddefinition_is_unique_and_more.py`
```python
# Generated by Django 6.0.2 on 2026-02-25 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customfielddefinition',
            name='is_unique',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customfielddefinition',
            name='select_options',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='customfielddefinition',
            name='field_type',
            field=models.CharField(choices=[('TEXT', 'Text'), ('NUMBER', 'Number'), ('DATE', 'Date'), ('BOOLEAN', 'Boolean'), ('SELECT', 'Select'), ('FILE', 'File')], max_length=16),
        ),
    ]

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
- `catalog/models.py`
- `catalog/serializers.py`
- `catalog/views.py`
- `catalog/urls.py`
- `catalog/tests.py`
- `catalog/admin.py`
- `catalog/apps.py`
- `catalog/migrations/0001_initial.py`
- `catalog/migrations/0002_customfielddefinition_is_unique_and_more.py`
- `catalog/management/commands/seed_initial_categories.py`

