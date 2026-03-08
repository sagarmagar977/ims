from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NotificationDelivery, NotificationStatus
from .observability import current_operational_metrics, evaluate_slo_breaches


def _webhook_token_is_valid(request):
    configured = (getattr(settings, "NOTIFICATION_WEBHOOK_TOKEN", "") or "").strip()
    if not configured:
        return True
    return request.headers.get("X-Webhook-Token", "").strip() == configured


class TwilioSMSStatusWebhookView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not _webhook_token_is_valid(request):
            return Response({"detail": "Unauthorized webhook token."}, status=status.HTTP_401_UNAUTHORIZED)

        sid = request.data.get("MessageSid")
        message_status = (request.data.get("MessageStatus") or "").lower()
        if not sid:
            return Response({"detail": "MessageSid is required."}, status=status.HTTP_400_BAD_REQUEST)

        delivery = NotificationDelivery.objects.filter(provider="twilio", provider_message_id=sid).first()
        if not delivery:
            return Response({"detail": "Delivery record not found."}, status=status.HTTP_404_NOT_FOUND)

        if message_status in {"delivered", "read"}:
            delivery.mark_delivered()
        elif message_status in {"failed", "undelivered", "canceled"}:
            delivery.mark_failed(f"Twilio status: {message_status}")
        else:
            delivery.status = NotificationStatus.SENT
            delivery.save(update_fields=["status", "updated_at"])

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class SendGridEventWebhookView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not _webhook_token_is_valid(request):
            return Response({"detail": "Unauthorized webhook token."}, status=status.HTTP_401_UNAUTHORIZED)

        events = request.data
        if not isinstance(events, list):
            return Response({"detail": "Expected a list of events."}, status=status.HTTP_400_BAD_REQUEST)

        for event in events:
            if not isinstance(event, dict):
                continue
            delivery_id = str(event.get("delivery_id") or "").strip()
            if not delivery_id.isdigit():
                continue
            delivery = NotificationDelivery.objects.filter(id=int(delivery_id), provider="sendgrid").first()
            if not delivery:
                continue

            event_name = (event.get("event") or "").lower()
            if event_name == "delivered":
                delivery.mark_delivered()
            elif event_name in {"processed", "deferred"}:
                delivery.status = NotificationStatus.SENT
                delivery.save(update_fields=["status", "updated_at"])
            elif event_name in {"bounce", "dropped", "blocked", "spamreport"}:
                delivery.mark_failed(f"SendGrid event: {event_name}")

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class OperationalStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(current_operational_metrics(), status=status.HTTP_200_OK)


class SLOStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        metrics = current_operational_metrics()
        breaches = evaluate_slo_breaches(metrics)
        return Response({"breaches": breaches, "healthy": len(breaches) == 0, "metrics": metrics}, status=status.HTTP_200_OK)
