import json
import logging
import base64

import requests
from django.conf import settings
from django.core.mail import send_mail

from common.models import NotificationChannel, NotificationDelivery

logger = logging.getLogger(__name__)


def _default_metadata(metadata):
    return metadata if isinstance(metadata, dict) else {}


def _send_sendgrid_email(delivery, subject, body):
    payload = {
        "personalizations": [{"to": [{"email": delivery.recipient}], "custom_args": {"delivery_id": str(delivery.id)}}],
        "from": {"email": getattr(settings, "DEFAULT_FROM_EMAIL", "ims@localhost")},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }
    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
        },
        timeout=15,
    )
    response.raise_for_status()
    message_id = response.headers.get("X-Message-Id", "")
    delivery.mark_sent(provider_message_id=message_id)


def send_email_notification(subject, body, recipients, metadata=None):
    provider = getattr(settings, "NOTIFICATION_EMAIL_PROVIDER", "django").strip().lower()
    deliveries = []
    for recipient in recipients:
        if not recipient:
            continue
        delivery = NotificationDelivery.objects.create(
            channel=NotificationChannel.EMAIL,
            provider=provider,
            recipient=recipient,
            subject=subject[:255],
            message=body,
            metadata=_default_metadata(metadata),
        )
        deliveries.append(delivery)
        try:
            if provider == "sendgrid":
                if not getattr(settings, "SENDGRID_API_KEY", ""):
                    raise ValueError("SENDGRID_API_KEY is not configured.")
                _send_sendgrid_email(delivery, subject, body)
            else:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "ims@localhost"),
                    recipient_list=[recipient],
                    fail_silently=False,
                )
                delivery.mark_sent()
        except Exception as exc:
            logger.exception("Failed to send email notification to %s via %s", recipient, provider)
            delivery.mark_failed(exc)
    return deliveries


def _send_twilio_sms(delivery, body):
    account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
    auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
    from_phone = getattr(settings, "TWILIO_FROM_PHONE", "")
    if not account_sid or not auth_token or not from_phone:
        raise ValueError("TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_PHONE are required.")

    twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    encoded_auth = base64.b64encode(f"{account_sid}:{auth_token}".encode("utf-8")).decode("ascii")
    response = requests.post(
        twilio_url,
        data={
            "From": from_phone,
            "To": delivery.recipient,
            "Body": body,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_auth}",
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    delivery.mark_sent(provider_message_id=payload.get("sid", ""))


def send_sms_notification(message, recipients, metadata=None):
    provider = getattr(settings, "NOTIFICATION_SMS_PROVIDER", "disabled").strip().lower()
    deliveries = []
    if provider == "disabled":
        return deliveries

    for recipient in recipients:
        if not recipient:
            continue
        delivery = NotificationDelivery.objects.create(
            channel=NotificationChannel.SMS,
            provider=provider,
            recipient=recipient,
            message=message,
            metadata=_default_metadata(metadata),
        )
        deliveries.append(delivery)
        try:
            if provider == "twilio":
                _send_twilio_sms(delivery, message)
            else:
                logger.info("SMS console provider: to=%s message=%s", recipient, message)
                delivery.mark_sent()
        except Exception as exc:
            logger.exception("Failed to send SMS notification to %s via %s", recipient, provider)
            delivery.mark_failed(exc)
    return deliveries


def send_low_stock_alert_for_stock(stock, trigger):
    subject = f"Low stock alert: {stock.item.title}"
    message = (
        f"Item: {stock.item.title}\n"
        f"Current quantity: {stock.quantity}\n"
        f"Minimum threshold: {stock.min_threshold}\n"
        f"Office: {stock.item.office.name}\n"
    )
    metadata = {
        "event": "low_stock_alert",
        "trigger": trigger,
        "stock_id": stock.id,
        "item_id": stock.item_id,
    }
    recipients = [email for email in getattr(settings, "LOW_STOCK_ALERT_EMAILS", []) if email]
    sms_recipients = [phone for phone in getattr(settings, "LOW_STOCK_ALERT_SMS", []) if phone]
    email_deliveries = send_email_notification(subject=subject, body=message, recipients=recipients, metadata=metadata)
    sms_deliveries = send_sms_notification(message=message, recipients=sms_recipients, metadata=metadata)
    return email_deliveries + sms_deliveries
