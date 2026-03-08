from django.urls import path

from .views import OperationalStatusView, SLOStatusView, SendGridEventWebhookView, TwilioSMSStatusWebhookView

urlpatterns = [
    path("integrations/webhooks/twilio/sms-status/", TwilioSMSStatusWebhookView.as_view(), name="twilio-sms-webhook"),
    path("integrations/webhooks/sendgrid/events/", SendGridEventWebhookView.as_view(), name="sendgrid-events-webhook"),
    path("observability/status/", OperationalStatusView.as_view(), name="observability-status"),
    path("observability/slo/", SLOStatusView.as_view(), name="observability-slo"),
]
