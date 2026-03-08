from rest_framework import status
from rest_framework.test import APITestCase

from common.models import BackupRun, JobRunStatus, NotificationChannel, NotificationDelivery, NotificationStatus
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


class NotificationWebhookTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="admin2",
            password="admin12345",
            email="admin2@example.com",
        )
        self.client.force_authenticate(user=self.user)

    def test_twilio_webhook_marks_delivery_as_delivered(self):
        delivery = NotificationDelivery.objects.create(
            channel=NotificationChannel.SMS,
            provider="twilio",
            recipient="+15550000000",
            message="Stock alert",
            status=NotificationStatus.SENT,
            provider_message_id="SM123",
        )
        payload = {"MessageSid": "SM123", "MessageStatus": "delivered"}
        response = self.client.post("/api/integrations/webhooks/twilio/sms-status/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, NotificationStatus.DELIVERED)

    def test_sendgrid_webhook_marks_delivery_as_failed(self):
        delivery = NotificationDelivery.objects.create(
            channel=NotificationChannel.EMAIL,
            provider="sendgrid",
            recipient="ops@example.com",
            message="Daily report",
            status=NotificationStatus.SENT,
        )
        payload = [{"event": "bounce", "delivery_id": str(delivery.id)}]
        response = self.client.post("/api/integrations/webhooks/sendgrid/events/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, NotificationStatus.FAILED)


class ObservabilityViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="ops-admin",
            password="admin12345",
            email="ops-admin@example.com",
        )
        self.client.force_authenticate(user=self.user)

    def test_observability_status_endpoint(self):
        BackupRun.objects.create(status=JobRunStatus.SUCCESS, backup_file="x:/tmp/test.json.gz")
        response = self.client.get("/api/observability/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("latest_backup", response.data)

    def test_observability_slo_endpoint(self):
        response = self.client.get("/api/observability/slo/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("healthy", response.data)
        self.assertIn("breaches", response.data)
