# Chapter 35 — Deep Dive: Test Suite and `.smoke_test.py`

## Build Roadmap Position
- Stage: Deep Dive
- You are here: Chapter 35
- Before this: Chapter 34
- After this: Chapter 36

## Learning Objectives
- Understand what behaviors are currently covered by automated tests.
- Identify coverage gaps visible from existing test files.
- `common/tests.py`

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 35 — Deep Dive: Test Suite and `.smoke_test.py`

## Learning Goals
- Understand what behaviors are currently covered by automated tests.
- Identify coverage gaps visible from existing test files.

## Reference Files
- `common/tests.py`
- `users/tests.py`
- `hierarchy/tests.py`
- `catalog/tests.py`
- `inventory/tests.py`
- `actions/tests.py`
- `audit/tests.py`
- `reports/tests.py`
- `.smoke_test.py`

## Test Coverage Map
- `common/tests.py`: deprecation headers for `/api/*` vs `/api/v1/*`.
- `users/tests.py`: self-privilege escalation prevention.
- `hierarchy/tests.py`: office write matrix by role.
- `catalog/tests.py`: category write matrix by role.
- `inventory/tests.py`: office scoping, role write restrictions, stock balance mutation, audit-on-bulk-import.
- `actions/tests.py`: assignment role matrix and audit-on-bulk-import.
- `audit/tests.py`: audit logs are read-only via API.
- `reports/tests.py`: export endpoint correctness (Excel/PDF signatures) and v1 report endpoint.

## `.smoke_test.py` role
- Procedural API sanity script that:
  - ensures admin/token,
  - exercises dashboard/report endpoints,
  - creates sample inventory/assignment/stock transaction,
  - checks summary/audit endpoints.

## Observed Gaps (from repository tests)
- No dedicated tests for settings env parsing branches.
- No dedicated tests for all report filters/fiscal-year edge cases.
- No dedicated tests for command modules.

## Chapter 35 Outcome
You now have a precise view of current automated verification coverage and the remaining untested paths.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
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

### File: `users/tests.py`
```python
from rest_framework import status
from rest_framework.test import APITestCase

from hierarchy.models import Office, OfficeLevels
from users.models import User, UserRoles


class UserPrivilegeEscalationTests(APITestCase):
    def setUp(self):
        self.central = Office.objects.create(name="Central", level=OfficeLevels.CENTRAL, location_code="CENTRAL-1")
        self.user = User.objects.create_user(
            username="ward_user",
            password="pass12345",
            role=UserRoles.WARD_OFFICER,
            office=self.central,
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_self_update_cannot_change_privileged_fields(self):
        payload = {
            "role": UserRoles.SUPER_ADMIN,
            "is_active": False,
        }
        response = self.client.patch(f"/api/users/{self.user.id}/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, UserRoles.WARD_OFFICER)
        self.assertTrue(self.user.is_active)

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

### File: `inventory/tests.py`
```python
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from audit.models import InventoryActionType, InventoryAuditLog
from catalog.models import Category
from hierarchy.models import Office, OfficeLevels
from users.models import User, UserRoles

from .models import ConsumableStock, InventoryItem, InventoryItemType


class InventoryAccessAndTransactionTests(APITestCase):
    def setUp(self):
        self.central = Office.objects.create(name="Central", level=OfficeLevels.CENTRAL, location_code="C-1")
        self.province_1 = Office.objects.create(
            name="Province 1", level=OfficeLevels.PROVINCIAL, parent_office=self.central, location_code="P1"
        )
        self.province_2 = Office.objects.create(
            name="Province 2", level=OfficeLevels.PROVINCIAL, parent_office=self.central, location_code="P2"
        )
        self.ward_11 = Office.objects.create(
            name="Ward 11", level=OfficeLevels.WARD, parent_office=self.province_1, location_code="W11"
        )

        self.fixed_cat = Category.objects.create(name="Laptop", is_consumable=False)
        self.cons_cat = Category.objects.create(name="Toner", is_consumable=True)

        self.provincial_user = User.objects.create_user(
            username="prov1", password="pass12345", role=UserRoles.PROVINCIAL_ADMIN, office=self.province_1
        )
        self.finance_user = User.objects.create_user(
            username="finance1", password="pass12345", role=UserRoles.FINANCE, office=self.central
        )
        self.ward_user = User.objects.create_user(
            username="ward11", password="pass12345", role=UserRoles.WARD_OFFICER, office=self.ward_11
        )

        InventoryItem.objects.create(
            category=self.fixed_cat,
            office=self.ward_11,
            title="Laptop P1",
            item_number="P1-ITM",
            item_type=InventoryItemType.FIXED_ASSET,
        )
        InventoryItem.objects.create(
            category=self.fixed_cat,
            office=self.province_2,
            title="Laptop P2",
            item_number="P2-ITM",
            item_type=InventoryItemType.FIXED_ASSET,
        )

    def test_provincial_user_sees_only_own_branch_items(self):
        self.client.force_authenticate(user=self.provincial_user)
        response = self.client.get("/api/inventory-items/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [item["title"] for item in response.data["results"]]
        self.assertIn("Laptop P1", titles)
        self.assertNotIn("Laptop P2", titles)

    def test_finance_role_is_read_only(self):
        self.client.force_authenticate(user=self.finance_user)
        payload = {
            "category": self.fixed_cat.id,
            "office": self.central.id,
            "title": "Blocked Item",
            "item_number": "FIN-1",
            "item_type": "FIXED_ASSET",
            "status": "ACTIVE",
        }
        response = self.client.post("/api/inventory-items/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ward_role_cannot_create_inventory_item(self):
        self.client.force_authenticate(user=self.ward_user)
        payload = {
            "category": self.fixed_cat.id,
            "office": self.ward_11.id,
            "title": "Ward Created Item",
            "item_number": "WARD-1",
            "item_type": "FIXED_ASSET",
            "status": "ACTIVE",
        }
        response = self.client.post("/api/inventory-items/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_stock_transaction_updates_balance(self):
        self.client.force_authenticate(user=self.provincial_user)
        item = InventoryItem.objects.create(
            category=self.cons_cat,
            office=self.ward_11,
            title="Toner A",
            item_number="CON-1",
            item_type=InventoryItemType.CONSUMABLE,
        )
        stock = ConsumableStock.objects.create(item=item, initial_quantity=50, quantity=50, min_threshold=10, unit="pcs")
        tx_payload = {
            "stock": stock.id,
            "transaction_type": "STOCK_OUT",
            "quantity": "5",
            "status": "ON_BOARDED",
            "amount": "5",
            "department": "Stores",
            "description": "Issue",
        }
        response = self.client.post("/api/consumable-stock-transactions/", tx_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        stock.refresh_from_db()
        self.assertEqual(float(stock.quantity), 45.0)

    def test_inventory_bulk_import_creates_audit_logs(self):
        self.client.force_authenticate(user=self.provincial_user)
        csv_content = (
            "title,item_number,item_type,status,category,office,amount,price,currency,store,project,department,manufacturer,description\n"
            f"Laptop B,P1-NEW,FIXED_ASSET,ACTIVE,{self.fixed_cat.id},{self.ward_11.id},0,0,,Main,PRJ,IT,Dell,Imported row\n"
        ).encode("utf-8")
        upload = SimpleUploadedFile("items.csv", csv_content, content_type="text/csv")
        response = self.client.post("/api/inventory-items/bulk-import/", {"file": upload}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 1)
        self.assertEqual(
            InventoryAuditLog.objects.filter(action_type=InventoryActionType.CREATE, remarks__icontains="bulk import").count(),
            1,
        )

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

### File: `reports/tests.py`
```python
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category
from hierarchy.models import Office, OfficeLevels
from inventory.models import InventoryItem, InventoryItemType
from users.models import User


class ReportExportTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username="admin", password="admin123", email="admin@example.com")
        office = Office.objects.create(name="Central", level=OfficeLevels.CENTRAL, location_code="CENTRAL-1")
        category = Category.objects.create(name="Laptop", is_consumable=False)
        InventoryItem.objects.create(
            category=category,
            office=office,
            title="Laptop A",
            item_number="ITM-100",
            item_type=InventoryItemType.FIXED_ASSET,
            status="ACTIVE",
        )
        self.client.force_authenticate(user=self.user)

    def test_inventory_export_excel(self):
        response = self.client.get("/api/reports/inventory/export-excel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertTrue(response.content.startswith(b"PK"))

    def test_inventory_export_pdf(self):
        response = self.client.get("/api/reports/inventory/export-pdf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_v1_inventory_report_endpoint(self):
        response = self.client.get("/api/v1/reports/inventory/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `.smoke_test.py`
```python
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from catalog.models import Category
from hierarchy.models import Office, OfficeLevels
from inventory.models import InventoryItem

User = get_user_model()
admin, created = User.objects.get_or_create(username='admin', defaults={'email':'admin@example.com'})
if created:
    admin.is_staff = True
    admin.is_superuser = True
    admin.set_password('admin123')
    admin.save()
else:
    admin.set_password('admin123')
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()

office, _ = Office.objects.get_or_create(name='Central Office', defaults={'level': OfficeLevels.CENTRAL, 'location_code': 'CENTRAL-001'})
if office.level != OfficeLevels.CENTRAL:
    office.level = OfficeLevels.CENTRAL
    office.location_code = office.location_code or 'CENTRAL-001'
    office.save()

laptop_cat, _ = Category.objects.get_or_create(name='Laptop', defaults={'is_consumable': False})
toner_cat, _ = Category.objects.get_or_create(name='Toner', defaults={'is_consumable': True})

client = APIClient()
resp = client.post('/api/auth/token/', {'username':'admin','password':'admin123'}, format='json')
print('token status', resp.status_code)
assert resp.status_code == 200, resp.content
access = resp.data['access']
client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

print('dashboard status', client.get('/api/reports/dashboard-summary/').status_code)
print('recent activities status', client.get('/api/reports/recent-inventory-activities/').status_code)

item_payload = {
    'title': 'Laptop - Dell 5420',
    'item_number': 'ITM-0001',
    'item_type': 'FIXED_ASSET',
    'status': 'ACTIVE',
    'category': laptop_cat.id,
    'office': office.id,
    'amount': '1',
    'price': '1200.00',
    'currency': 'NPR'
}
item_resp = client.post('/api/inventory-items/', item_payload, format='json')
print('create item status', item_resp.status_code)
if item_resp.status_code not in (200, 201):
    print(item_resp.data)

item = InventoryItem.objects.filter(item_number='ITM-0001').first()
if item:
    assign_resp = client.post('/api/item-assignments/', {
        'item': item.id,
        'assigned_to_user': admin.id,
        'handover_date': '2026-02-25',
        'assign_till': '2026-03-25',
        'status': 'ASSIGNED'
    }, format='json')
    print('create assignment status', assign_resp.status_code)
    if assign_resp.status_code not in (200, 201):
        print(assign_resp.data)

cons_payload = {
    'title': 'Toner Cartridge',
    'item_number': 'CON-0001',
    'item_type': 'CONSUMABLE',
    'status': 'ACTIVE',
    'category': toner_cat.id,
    'office': office.id,
    'amount': '1'
}
cons_resp = client.post('/api/inventory-items/', cons_payload, format='json')
print('create consumable item status', cons_resp.status_code)
if cons_resp.status_code not in (200, 201):
    print(cons_resp.data)

cons_item = InventoryItem.objects.filter(item_number='CON-0001').first()
if cons_item:
    stock_resp = client.post('/api/consumable-stocks/', {
        'item': cons_item.id,
        'initial_quantity': '100',
        'quantity': '100',
        'min_threshold': '20',
        'unit': 'pcs'
    }, format='json')
    print('create stock status', stock_resp.status_code)
    if stock_resp.status_code not in (200, 201):
        print(stock_resp.data)
    if stock_resp.status_code in (200, 201):
        tx_resp = client.post('/api/consumable-stock-transactions/', {
            'stock': stock_resp.data['id'],
            'transaction_type': 'STOCK_OUT',
            'quantity': '5',
            'status': 'ON_BOARDED',
            'amount': '5',
            'department': 'Stores',
            'description': 'Issue to office'
        }, format='json')
        print('create stock tx status', tx_resp.status_code)
        if tx_resp.status_code not in (200, 201):
            print(tx_resp.data)

print('assignee summary status', client.get('/api/item-assignments/summary-by-assignee/').status_code)
print('audit logs status', client.get('/api/audit-logs/').status_code)
print('stock transactions list status', client.get('/api/consumable-stock-transactions/').status_code)

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
- `common/tests.py`
- `users/tests.py`
- `hierarchy/tests.py`
- `catalog/tests.py`
- `inventory/tests.py`
- `actions/tests.py`
- `audit/tests.py`
- `reports/tests.py`
- `.smoke_test.py`

