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
