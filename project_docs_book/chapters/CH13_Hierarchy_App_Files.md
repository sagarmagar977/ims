# Chapter 13 — Hierarchy App Files

## Build Roadmap Position
- Stage: Core Domain
- You are here: Chapter 13
- Before this: Chapter 12
- After this: Chapter 14

## Learning Objectives
- Understand the office hierarchy data model.
- Learn how hierarchy APIs apply role and scope controls.
- Map how hierarchy data supports the rest of the system.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 13 — Hierarchy App Files

## Learning Goals
- Understand the office hierarchy data model.
- Learn how hierarchy APIs apply role and scope controls.
- Map how hierarchy data supports the rest of the system.

## Reference Files
- `hierarchy/models.py`
- `hierarchy/serializers.py`
- `hierarchy/views.py`
- `hierarchy/urls.py`
- `hierarchy/tests.py`
- `hierarchy/admin.py`
- `hierarchy/apps.py`
- `hierarchy/migrations/0001_initial.py`
- `hierarchy/migrations/0002_alter_office_level.py`

## File Breakdown

## 1) `hierarchy/models.py`
### `OfficeLevels`
- Enum choices for office levels:
  - `CENTRAL`
  - `PROVINCIAL`
  - `LOCAL`
  - `WARD`

### `Office`
Key fields:
- `name`
- `level` (choice field)
- `parent_office` (self FK, `PROTECT`, nullable)
- `location_code` (unique)

Model characteristics:
- supports tree/hierarchical structure via self-reference.
- uses indexes on `level` and `location_code`.
- `__str__` includes name and level.

## 2) `hierarchy/serializers.py`
### `OfficeSerializer`
- Exposes fields:
  - `id`, `name`, `level`, `parent_office`, `location_code`
- `id` is read-only.

No custom validation logic is implemented in serializer file.

## 3) `hierarchy/views.py`
### `OfficeViewSet`
- `ModelViewSet` for office CRUD.
- Adds filter/search/ordering support.
- Permission class: `IMSAccessPermission`.
- Queryset scope:
  - `scope_queryset_by_user(queryset, request.user, "id")`

Meaning:
- office visibility is constrained by role/office-scoping rules from `common/access.py`.

## 4) `hierarchy/urls.py`
- Registers `OfficeViewSet` via DRF router at `offices`.
- Effective routes:
  - `/api/offices/`
  - `/api/v1/offices/`

## 5) `hierarchy/tests.py`
### `OfficeRoleMatrixTests`
Covers write permissions:
- central admin can create office (`201` expected).
- provincial admin cannot create office (`403` expected).

This validates hierarchy write policy matrix enforcement.

## 6) `hierarchy/admin.py`
- Registers `Office` model in Django admin.

## 7) `hierarchy/apps.py`
- Declares app config `HierarchyConfig` with `name='hierarchy'`.

## 8) Migration Evolution
- `0001_initial.py`:
  - creates `Office` model and initial indexes.
  - initial level choice included a typo variant (`PROVENCIAL`).
- `0002_alter_office_level.py`:
  - corrects choices to `PROVINCIAL`.

## Hierarchy App Responsibilities (Observed)
- Stores official office structure as a tree.
- Provides office CRUD API with role-based write restrictions.
- Serves as foundational reference for user office assignment and scope filtering across apps.

## Architecture Notes
- `on_delete=PROTECT` on `parent_office` helps preserve tree integrity.
- Office tree is consumed by scope logic (`get_descendant_office_ids`) in shared access module.
- Hierarchy is a core dependency for users, inventory scoping, assignments, and reports.

## Chapter 13 Outcome
You now have a complete map of the hierarchy app: office tree schema, API surface, permission behavior, migration correction history, and its system-wide role in access scoping.
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

### File: `hierarchy/serializers.py`
```python
from rest_framework import serializers

from .models import Office


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ["id", "name", "level", "parent_office", "location_code"]
        read_only_fields = ["id"]

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

### File: `hierarchy/urls.py`
```python
from rest_framework.routers import DefaultRouter

from .views import OfficeViewSet

router = DefaultRouter()
router.register(r"offices", OfficeViewSet, basename="office")

urlpatterns = router.urls

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `hierarchy/tests.py`
```python
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Office, OfficeLevels
from users.models import User, UserRoles


class OfficeRoleMatrixTests(APITestCase):
    def setUp(self):
        self.central = Office.objects.create(name="Central", level=OfficeLevels.CENTRAL, location_code="CEN-1")
        self.central_admin = User.objects.create_user(
            username="central_admin",
            password="pass12345",
            role=UserRoles.CENTRAL_ADMIN,
            office=self.central,
        )
        self.provincial_admin = User.objects.create_user(
            username="provincial_admin",
            password="pass12345",
            role=UserRoles.PROVINCIAL_ADMIN,
            office=self.central,
        )

    def test_central_admin_can_create_office(self):
        self.client.force_authenticate(user=self.central_admin)
        payload = {"name": "Province 1", "level": OfficeLevels.PROVINCIAL, "parent_office": self.central.id, "location_code": "P1"}
        response = self.client.post("/api/offices/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_provincial_admin_cannot_create_office(self):
        self.client.force_authenticate(user=self.provincial_admin)
        payload = {"name": "Province 2", "level": OfficeLevels.PROVINCIAL, "parent_office": self.central.id, "location_code": "P2"}
        response = self.client.post("/api/offices/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `hierarchy/admin.py`
```python
from django.contrib import admin
from .models import *


admin.site.register(Office)




# Register your models here.


```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `hierarchy/apps.py`
```python
from django.apps import AppConfig


class HierarchyConfig(AppConfig):
    name = 'hierarchy'

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `hierarchy/migrations/0001_initial.py`
```python
# Generated by Django 6.0.2 on 2026-02-24 08:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Office',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('level', models.CharField(choices=[('CENTRAL', 'central'), ('PROVENCIAL', 'provencial'), ('LOCAL', 'local'), ('WARD', 'ward')], max_length=16)),
                ('location_code', models.CharField(max_length=64, unique=True)),
                ('parent_office', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='children', to='hierarchy.office')),
            ],
            options={
                'indexes': [models.Index(fields=['level'], name='hierarchy_o_level_7923d8_idx'), models.Index(fields=['location_code'], name='hierarchy_o_locatio_10a5d7_idx')],
            },
        ),
    ]

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `hierarchy/migrations/0002_alter_office_level.py`
```python
# Generated by Django 6.0.2 on 2026-02-25 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hierarchy', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='office',
            name='level',
            field=models.CharField(choices=[('CENTRAL', 'central'), ('PROVINCIAL', 'provincial'), ('LOCAL', 'local'), ('WARD', 'ward')], max_length=16),
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
- `hierarchy/models.py`
- `hierarchy/serializers.py`
- `hierarchy/views.py`
- `hierarchy/urls.py`
- `hierarchy/tests.py`
- `hierarchy/admin.py`
- `hierarchy/apps.py`
- `hierarchy/migrations/0001_initial.py`
- `hierarchy/migrations/0002_alter_office_level.py`

