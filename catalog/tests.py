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
