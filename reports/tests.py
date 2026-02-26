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
