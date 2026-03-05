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
