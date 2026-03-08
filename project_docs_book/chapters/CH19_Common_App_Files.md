# Chapter 19 — Common App Files

## Build Roadmap Position
- Stage: Core Domain
- You are here: Chapter 19
- Before this: Chapter 18
- After this: Chapter 20

## Learning Objectives
- Understand shared permission and data-scope rules.
- Trace middleware behavior for API deprecation signaling.
- Learn bootstrap/seed command responsibilities.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 19 — Common App Files

## Learning Goals
- Understand shared permission and data-scope rules.
- Trace middleware behavior for API deprecation signaling.
- Learn bootstrap/seed command responsibilities.

## Reference Files
- `common/access.py`
- `common/permissions.py`
- `common/middleware.py`
- `common/views.py`
- `common/models.py`
- `common/tests.py`
- `common/admin.py`
- `common/apps.py`
- `common/management/commands/bootstrap_admin.py`
- `common/management/commands/seed_prd_data.py`

## File Breakdown

## 1) `common/permissions.py`
- Defines role sets:
  - read-only: `FINANCE`, `AUDIT`
  - write-capable baseline roles
- `WRITE_ROLE_MATRIX` maps viewset basename to allowed write roles.
- `IMSAccessPermission`:
  - allows staff/superuser,
  - allows authenticated reads,
  - denies writes for read-only roles,
  - enforces per-resource role matrix for writes.

## 2) `common/access.py`
- `get_descendant_office_ids(root_office_id)`: iterative traversal of office tree.
- `get_accessible_office_ids(user)`:
  - global roles and staff/superuser => unrestricted (`None`),
  - scoped roles => office subtree (or own office for ward),
  - others => empty list.
- `scope_queryset_by_user(queryset, user, office_lookup)` applies filtered office visibility.

## 3) `common/middleware.py`
- `LegacyApiDeprecationMiddleware` adds headers on `/api/*` (excluding `/api/v1/*`):
  - `Deprecation: true`
  - `Sunset: Wed, 31 Dec 2026 23:59:59 GMT`
  - `Link: </api/v1/>; rel="successor-version"`

## 4) Management commands
- `bootstrap_admin.py`:
  - creates/updates bootstrap admin from env vars,
  - sets staff/superuser flags and optional `role`.
- `seed_prd_data.py`:
  - idempotently seeds offices, users, custom fields, inventory, assignments, transactions, audit logs,
  - supports `--dry-run` with transaction rollback,
  - invokes `seed_initial_categories`.

## 5) Remaining common files
- `common/models.py`: placeholder only.
- `common/views.py`: placeholder only.
- `common/admin.py`: placeholder only.
- `common/apps.py`: defines `CommonConfig`.
- `common/tests.py`: verifies deprecation headers appear on `/api/*` and not on `/api/v1/*`.

## Chapter 19 Outcome
You now have the cross-cutting control map: RBAC, office scoping, API deprecation signaling, and bootstrap/seed automation.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
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

### File: `common/views.py`
```python
from django.shortcuts import render

# Create your views here.

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `common/models.py`
```python
from django.db import models

# Create your models here.

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `common/tests.py`
```python
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class LegacyApiDeprecationMiddlewareTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="admin",
            password="admin12345",
            email="admin@example.com",
        )
        self.client.force_authenticate(user=self.user)

    def test_legacy_api_path_gets_deprecation_headers(self):
        response = self.client.get("/api/offices/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers.get("Deprecation"), "true")
        self.assertIn("/api/v1/", response.headers.get("Link", ""))

    def test_v1_api_path_avoids_deprecation_headers(self):
        response = self.client.get("/api/v1/offices/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("Deprecation", response.headers)

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `common/admin.py`
```python
from django.contrib import admin

# Register your models here.

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `common/apps.py`
```python
from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = 'common'

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `common/management/commands/bootstrap_admin.py`
```python
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update the initial admin user from environment variables."

    def handle(self, *args, **options):
        username = (os.getenv("BOOTSTRAP_ADMIN_USERNAME") or "").strip()
        password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD") or ""
        email = (os.getenv("BOOTSTRAP_ADMIN_EMAIL") or "").strip()
        first_name = (os.getenv("BOOTSTRAP_ADMIN_FIRST_NAME") or "").strip()
        last_name = (os.getenv("BOOTSTRAP_ADMIN_LAST_NAME") or "").strip()

        if not username:
            self.stdout.write("BOOTSTRAP_ADMIN_USERNAME not set; skipping bootstrap admin.")
            return

        if not password:
            self.stdout.write("BOOTSTRAP_ADMIN_PASSWORD not set; skipping bootstrap admin.")
            return

        User = get_user_model()
        defaults = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        }

        role_field = User._meta.get_field("role") if any(field.name == "role" for field in User._meta.fields) else None
        if role_field is not None:
            defaults["role"] = "SUPER_ADMIN"

        user, created = User.objects.get_or_create(username=username, defaults=defaults)

        changed_fields = []
        for field, value in defaults.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                changed_fields.append(field)

        if not user.check_password(password):
            user.set_password(password)
            changed_fields.append("password")

        if created:
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created bootstrap admin '{username}'."))  # noqa: B950
            return

        if changed_fields:
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Updated bootstrap admin '{username}'."))  # noqa: B950
            return

        self.stdout.write(f"Bootstrap admin '{username}' already configured.")

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `common/management/commands/seed_prd_data.py`
```python
from datetime import date, datetime, timezone
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from actions.models import AssignmentStatus, ItemAssignment, ItemCondition
from audit.models import InventoryActionType, InventoryAuditLog
from catalog.models import Category, CustomFieldDefinition, CustomFieldType
from hierarchy.models import Office, OfficeLevels
from inventory.models import (
    ConsumableStock,
    ConsumableStockTransaction,
    FixedAsset,
    InventoryItem,
    InventoryItemType,
    InventoryStatus,
    StockTransactionType,
)
from users.models import User, UserRoles


OFFICES = [
    ("DoNIDCR Central Office", OfficeLevels.CENTRAL, None, "NPL-CENTRAL-001"),
    ("Province 1 Office", OfficeLevels.PROVINCIAL, "NPL-CENTRAL-001", "NPL-P1-001"),
    ("Province 2 Office", OfficeLevels.PROVINCIAL, "NPL-CENTRAL-001", "NPL-P2-001"),
    ("Kathmandu Metropolitan Office", OfficeLevels.LOCAL, "NPL-P1-001", "NPL-L1-001"),
    ("Lalitpur Metropolitan Office", OfficeLevels.LOCAL, "NPL-P1-001", "NPL-L1-002"),
    ("Ward 1 Registration Point", OfficeLevels.WARD, "NPL-L1-001", "NPL-W1-001"),
    ("Ward 2 Registration Point", OfficeLevels.WARD, "NPL-L1-001", "NPL-W1-002"),
]

USERS = [
    ("superadmin", "SUPER_ADMIN", True, "NPL-CENTRAL-001"),
    ("central_admin", "CENTRAL_ADMIN", True, "NPL-CENTRAL-001"),
    ("store_keeper", "CENTRAL_PROCUREMENT_STORE", False, "NPL-CENTRAL-001"),
    ("prov_admin_p1", "PROVINCIAL_ADMIN", False, "NPL-P1-001"),
    ("local_admin_ktm", "LOCAL_ADMIN", False, "NPL-L1-001"),
    ("ward_officer_1", "WARD_OFFICER", False, "NPL-W1-001"),
    ("finance_user", "FINANCE", False, "NPL-CENTRAL-001"),
    ("audit_user", "AUDIT", False, "NPL-CENTRAL-001"),
]

CUSTOM_FIELDS = [
    ("Laptop", "RAM", CustomFieldType.SELECT, True, False, ["8GB", "16GB", "32GB"]),
    ("Laptop", "Processor", CustomFieldType.TEXT, True, False, []),
    ("Laptop", "Storage", CustomFieldType.SELECT, True, False, ["256GB SSD", "512GB SSD", "1TB SSD"]),
    ("Printer", "Model", CustomFieldType.TEXT, True, False, []),
    ("Printer", "Ink Type", CustomFieldType.SELECT, True, False, ["Inkjet", "Laser Toner"]),
    ("Biometric Device", "Vendor", CustomFieldType.TEXT, True, False, []),
    ("Registration Forms", "Form Type", CustomFieldType.SELECT, True, False, ["Birth", "Death", "Marriage"]),
    ("Stationery", "Unit", CustomFieldType.TEXT, True, False, []),
    ("Toner/Ink", "Color", CustomFieldType.SELECT, False, False, ["Black", "Cyan", "Magenta", "Yellow"]),
]

ITEMS = [
    {
        "item_number": "FA-0001",
        "title": "Dell Latitude 5440",
        "category": "Laptop",
        "office_code": "NPL-W1-001",
        "item_type": InventoryItemType.FIXED_ASSET,
        "status": InventoryStatus.ACTIVE,
        "amount": Decimal("120000.00"),
        "price": Decimal("120000.00"),
        "currency": "NPR",
        "department": "Registration",
        "manufacturer": "Dell",
        "purchased_date": date(2025, 7, 20),
        "dynamic_data": {"RAM": "16GB", "Processor": "Intel i7", "Storage": "512GB SSD"},
        "fixed_asset": {
            "asset_tag": "LAP-W1-0001",
            "serial_number": "SN-LAP-0001",
            "purchase_date": date(2025, 7, 20),
            "warranty_expiry_date": date(2028, 7, 20),
        },
    },
    {
        "item_number": "FA-0002",
        "title": "HP LaserJet Pro",
        "category": "Printer",
        "office_code": "NPL-L1-001",
        "item_type": InventoryItemType.FIXED_ASSET,
        "status": InventoryStatus.ACTIVE,
        "amount": Decimal("45000.00"),
        "price": Decimal("45000.00"),
        "currency": "NPR",
        "department": "Office Operations",
        "manufacturer": "HP",
        "purchased_date": date(2025, 8, 10),
        "dynamic_data": {"Model": "M404dn", "Ink Type": "Laser Toner"},
        "fixed_asset": {
            "asset_tag": "PRN-L1-0001",
            "serial_number": "SN-PRN-0001",
            "purchase_date": date(2025, 8, 10),
            "warranty_expiry_date": date(2027, 8, 10),
        },
    },
    {
        "item_number": "CON-0001",
        "title": "Citizen Registration Form",
        "category": "Registration Forms",
        "office_code": "NPL-W1-001",
        "item_type": InventoryItemType.CONSUMABLE,
        "status": InventoryStatus.ACTIVE,
        "amount": Decimal("10000.00"),
        "price": Decimal("10.00"),
        "currency": "NPR",
        "department": "Registration",
        "manufacturer": "Govt Printing Press",
        "purchased_date": date(2025, 7, 25),
        "dynamic_data": {"Form Type": "Birth"},
        "consumable_stock": {
            "initial_quantity": Decimal("1000"),
            "quantity": Decimal("920"),
            "min_threshold": Decimal("200"),
            "unit": "pcs",
        },
    },
    {
        "item_number": "CON-0002",
        "title": "A4 Office Paper",
        "category": "Stationery",
        "office_code": "NPL-L1-001",
        "item_type": InventoryItemType.CONSUMABLE,
        "status": InventoryStatus.ACTIVE,
        "amount": Decimal("15000.00"),
        "price": Decimal("500.00"),
        "currency": "NPR",
        "department": "Admin",
        "manufacturer": "Nepal Paper Co",
        "purchased_date": date(2025, 9, 1),
        "dynamic_data": {"Unit": "ream"},
        "consumable_stock": {
            "initial_quantity": Decimal("100"),
            "quantity": Decimal("60"),
            "min_threshold": Decimal("20"),
            "unit": "ream",
        },
    },
]


class Command(BaseCommand):
    help = "Seed PRD-aligned sample data across core IMS tables (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing data.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        self.stdout.write("Seeding PRD-aligned data...")

        with transaction.atomic():
            call_command("seed_initial_categories", dry_run=dry_run, stdout=self.stdout)

            offices = self._seed_offices(dry_run=dry_run)
            users = self._seed_users(offices=offices, dry_run=dry_run)
            self._seed_custom_fields(dry_run=dry_run)
            items = self._seed_inventory(offices=offices, dry_run=dry_run)
            self._seed_assignments(items=items, users=users, offices=offices, dry_run=dry_run)
            self._seed_stock_transactions(items=items, users=users, dry_run=dry_run)
            self._seed_audit_logs(items=items, users=users, dry_run=dry_run)

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("Dry run enabled. Rolled back all changes."))

        self.stdout.write(self.style.SUCCESS("PRD seed completed."))

    def _seed_offices(self, dry_run=False):
        office_by_code = {o.location_code: o for o in Office.objects.all()}
        created = 0
        updated = 0

        for name, level, parent_code, code in OFFICES:
            parent = office_by_code.get(parent_code) if parent_code else None
            obj = Office.objects.filter(location_code=code).first()
            if obj is None:
                created += 1
                if not dry_run:
                    obj = Office.objects.create(name=name, level=level, parent_office=parent, location_code=code)
                office_by_code[code] = obj
                self.stdout.write(self.style.SUCCESS(f"{'Would create' if dry_run else 'Created'} office: {code}"))
                continue

            changed = False
            if obj.name != name:
                obj.name = name
                changed = True
            if obj.level != level:
                obj.level = level
                changed = True
            if obj.parent_office_id != (parent.id if parent else None):
                obj.parent_office = parent
                changed = True
            if changed:
                updated += 1
                if not dry_run:
                    obj.save(update_fields=["name", "level", "parent_office"])
                self.stdout.write(self.style.WARNING(f"{'Would update' if dry_run else 'Updated'} office: {code}"))
            office_by_code[code] = obj

        self.stdout.write(f"Offices: created={created}, updated={updated}, total={len(office_by_code)}")
        return office_by_code

    def _seed_users(self, offices, dry_run=False):
        users = {}
        created = 0
        updated = 0

        for username, role, is_staff, office_code in USERS:
            office = offices.get(office_code)
            defaults = {
                "email": f"{username}@ims.local",
                "first_name": username.replace("_", " ").title(),
                "role": role,
                "is_staff": is_staff,
                "is_active": True,
                "office": office,
            }
            obj = User.objects.filter(username=username).first()
            if obj is None:
                created += 1
                if not dry_run:
                    obj = User.objects.create(username=username, **defaults)
                    obj.set_password("ChangeMe123!")
                    obj.save(update_fields=["password"])
                self.stdout.write(self.style.SUCCESS(f"{'Would create' if dry_run else 'Created'} user: {username}"))
            else:
                changed = False
                for field, value in defaults.items():
                    if getattr(obj, field) != value:
                        setattr(obj, field, value)
                        changed = True
                if changed and not dry_run:
                    obj.save(update_fields=list(defaults.keys()))
                if changed:
                    updated += 1
                    self.stdout.write(self.style.WARNING(f"{'Would update' if dry_run else 'Updated'} user: {username}"))
            users[username] = obj

        self.stdout.write(f"Users: created={created}, updated={updated}, total={len(users)}")
        return users

    def _seed_custom_fields(self, dry_run=False):
        created = 0
        updated = 0
        skipped = 0
        for category_name, label, field_type, required, is_unique, select_options in CUSTOM_FIELDS:
            category = Category.objects.filter(name=category_name).first()
            if not category:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"Skipped custom field '{label}': category '{category_name}' not found"))
                continue

            obj = CustomFieldDefinition.objects.filter(category=category, label=label).first()
            if obj is None:
                created += 1
                if not dry_run:
                    CustomFieldDefinition.objects.create(
                        category=category,
                        label=label,
                        field_type=field_type,
                        required=required,
                        is_unique=is_unique,
                        select_options=select_options,
                    )
                self.stdout.write(self.style.SUCCESS(f"{'Would create' if dry_run else 'Created'} custom field: {category_name}::{label}"))
            else:
                changed = False
                if obj.field_type != field_type:
                    obj.field_type = field_type
                    changed = True
                if obj.required != required:
                    obj.required = required
                    changed = True
                if obj.is_unique != is_unique:
                    obj.is_unique = is_unique
                    changed = True
                if obj.select_options != select_options:
                    obj.select_options = select_options
                    changed = True
                if changed:
                    updated += 1
                    if not dry_run:
                        obj.save(update_fields=["field_type", "required", "is_unique", "select_options"])
                    self.stdout.write(self.style.WARNING(f"{'Would update' if dry_run else 'Updated'} custom field: {category_name}::{label}"))

        self.stdout.write(f"Custom fields: created={created}, updated={updated}, skipped={skipped}")

    def _seed_inventory(self, offices, dry_run=False):
        item_by_number = {}
        created = 0
        updated = 0

        for payload in ITEMS:
            category = Category.objects.get(name=payload["category"])
            office = offices[payload["office_code"]]
            defaults = {
                "title": payload["title"],
                "category": category,
                "office": office,
                "item_type": payload["item_type"],
                "status": payload["status"],
                "amount": payload["amount"],
                "price": payload["price"],
                "currency": payload["currency"],
                "department": payload["department"],
                "manufacturer": payload["manufacturer"],
                "purchased_date": payload["purchased_date"],
                "dynamic_data": payload["dynamic_data"],
            }

            obj = InventoryItem.objects.filter(item_number=payload["item_number"]).first()
            if obj is None:
                created += 1
                if not dry_run:
                    obj = InventoryItem.objects.create(item_number=payload["item_number"], **defaults)
                self.stdout.write(self.style.SUCCESS(f"{'Would create' if dry_run else 'Created'} item: {payload['item_number']}"))
            else:
                changed = False
                for field, value in defaults.items():
                    if getattr(obj, field) != value:
                        setattr(obj, field, value)
                        changed = True
                if changed:
                    updated += 1
                    if not dry_run:
                        obj.save(update_fields=list(defaults.keys()))
                    self.stdout.write(self.style.WARNING(f"{'Would update' if dry_run else 'Updated'} item: {payload['item_number']}"))

            if payload["item_type"] == InventoryItemType.FIXED_ASSET:
                fa_defaults = payload["fixed_asset"]
                if not dry_run and obj:
                    FixedAsset.objects.update_or_create(item=obj, defaults=fa_defaults)
            else:
                stock_defaults = payload["consumable_stock"]
                if not dry_run and obj:
                    ConsumableStock.objects.update_or_create(item=obj, defaults=stock_defaults)

            item_by_number[payload["item_number"]] = obj

        self.stdout.write(f"Inventory items: created={created}, updated={updated}, total={len(item_by_number)}")
        return item_by_number

    def _seed_assignments(self, items, users, offices, dry_run=False):
        assigned_item = items.get("FA-0001")
        returned_item = items.get("FA-0002")
        assigned_by = users.get("store_keeper")
        assigned_user = users.get("ward_officer_1")
        assigned_office = offices.get("NPL-L1-001")

        if not dry_run and assigned_item and assigned_by and assigned_user:
            ItemAssignment.objects.update_or_create(
                item=assigned_item,
                status=AssignmentStatus.ASSIGNED,
                defaults={
                    "assigned_to_user": assigned_user,
                    "assigned_to_office": None,
                    "assigned_by": assigned_by,
                    "handover_date": date(2025, 8, 1),
                    "assign_till": date(2026, 8, 1),
                    "handover_condition": ItemCondition.GOOD,
                    "remarks": "PRD seed: assigned laptop to ward officer",
                },
            )

        if not dry_run and returned_item and assigned_by and assigned_office:
            ItemAssignment.objects.update_or_create(
                item=returned_item,
                status=AssignmentStatus.RETURNED,
                defaults={
                    "assigned_to_user": None,
                    "assigned_to_office": assigned_office,
                    "assigned_by": assigned_by,
                    "handover_date": date(2025, 8, 12),
                    "assign_till": date(2025, 12, 31),
                    "returned_at": datetime(2025, 12, 20, 10, 30, tzinfo=timezone.utc),
                    "return_condition": ItemCondition.GOOD,
                    "handover_condition": ItemCondition.GOOD,
                    "remarks": "PRD seed: printer returned in good condition",
                },
            )

        self.stdout.write("Assignments: upserted 2 sample records")

    def _seed_stock_transactions(self, items, users, dry_run=False):
        if dry_run:
            self.stdout.write("Stock transactions: would upsert 2 sample records")
            return

        stock_item = items.get("CON-0001")
        performer = users.get("store_keeper")
        assignee = users.get("ward_officer_1")
        if not stock_item:
            self.stdout.write(self.style.WARNING("Stock transactions skipped: CON-0001 item not found"))
            return
        stock = ConsumableStock.objects.filter(item=stock_item).first()
        if not stock:
            self.stdout.write(self.style.WARNING("Stock transactions skipped: stock row for CON-0001 not found"))
            return

        in_txn, _ = ConsumableStockTransaction.objects.get_or_create(
            stock=stock,
            transaction_type=StockTransactionType.STOCK_IN,
            description="PRD seed opening stock adjustment",
            defaults={
                "quantity": Decimal("1000"),
                "balance_after": Decimal("1000"),
                "status": "COMPLETED",
                "amount": Decimal("10000"),
                "assigned_to": None,
                "performed_by": performer,
                "department": "Central Store",
            },
        )
        out_txn, _ = ConsumableStockTransaction.objects.get_or_create(
            stock=stock,
            transaction_type=StockTransactionType.STOCK_OUT,
            description="PRD seed issued to ward office",
            defaults={
                "quantity": Decimal("80"),
                "balance_after": Decimal("920"),
                "status": "COMPLETED",
                "amount": Decimal("800"),
                "assigned_to": assignee,
                "performed_by": performer,
                "department": "Ward Services",
            },
        )

        final_balance = out_txn.balance_after if out_txn else in_txn.balance_after
        if stock.quantity != final_balance:
            stock.quantity = final_balance
            stock.save(update_fields=["quantity"])

        self.stdout.write("Stock transactions: upserted 2 sample records")

    def _seed_audit_logs(self, items, users, dry_run=False):
        if dry_run:
            self.stdout.write("Audit logs: would upsert sample records")
            return

        actor = users.get("store_keeper")
        for item_number, item in items.items():
            if not item:
                continue
            InventoryAuditLog.objects.get_or_create(
                item=item,
                action_type=InventoryActionType.CREATE,
                remarks=f"PRD seed: created {item_number}",
                defaults={
                    "performed_by": actor,
                    "before_data": {},
                    "after_data": {
                        "item_number": item.item_number,
                        "title": item.title,
                        "status": item.status,
                        "item_type": item.item_type,
                    },
                },
            )

        assigned_item = items.get("FA-0001")
        returned_item = items.get("FA-0002")

        if assigned_item:
            InventoryAuditLog.objects.get_or_create(
                item=assigned_item,
                action_type=InventoryActionType.ASSIGN,
                remarks="PRD seed: assignment recorded",
                defaults={
                    "performed_by": actor,
                    "after_data": {"status": "ASSIGNED"},
                },
            )
        if returned_item:
            InventoryAuditLog.objects.get_or_create(
                item=returned_item,
                action_type=InventoryActionType.RETURN,
                remarks="PRD seed: return recorded",
                defaults={
                    "performed_by": actor,
                    "after_data": {"status": "RETURNED"},
                },
            )

        self.stdout.write("Audit logs: upserted sample records")

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
- `common/access.py`
- `common/permissions.py`
- `common/middleware.py`
- `common/views.py`
- `common/models.py`
- `common/tests.py`
- `common/admin.py`
- `common/apps.py`
- `common/management/commands/bootstrap_admin.py`
- `common/management/commands/seed_prd_data.py`

