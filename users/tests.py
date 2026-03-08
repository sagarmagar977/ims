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


class TokenLoginTests(APITestCase):
    def setUp(self):
        self.office = Office.objects.create(name="Central 2", level=OfficeLevels.CENTRAL, location_code="CENTRAL-2")
        self.user = User.objects.create_user(
            username="sagar",
            email="sagar@gmail.com",
            password="pass12345",
            role=UserRoles.CENTRAL_ADMIN,
            office=self.office,
            is_active=True,
        )

    def test_token_obtain_with_email(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {"email": "sagar@gmail.com", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_token_obtain_with_username_only_is_rejected(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {"username": "sagar", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
