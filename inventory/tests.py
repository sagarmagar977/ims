from rest_framework import status
from rest_framework.test import APITestCase

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
