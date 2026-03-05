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
