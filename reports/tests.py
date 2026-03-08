from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category
from common.tasks import periodic_inventory_report_generation
from hierarchy.models import Office, OfficeLevels
from inventory.models import InventoryItem, InventoryItemType
from .models import GeneratedReport, ReportGenerationStatus, ReportType
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

    def test_periodic_inventory_report_generation_task_creates_report(self):
        result = periodic_inventory_report_generation()
        report = GeneratedReport.objects.get(id=result["report_id"])
        self.assertEqual(report.report_type, ReportType.INVENTORY_DAILY_SUMMARY)
        self.assertEqual(report.status, ReportGenerationStatus.GENERATED)
        self.assertGreaterEqual(report.row_count, 1)
