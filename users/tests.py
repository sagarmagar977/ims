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
