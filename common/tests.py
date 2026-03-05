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
