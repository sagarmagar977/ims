from django.db import models
from django.utils import timezone


class NotificationChannel(models.TextChoices):
    EMAIL = "EMAIL", "Email"
    SMS = "SMS", "SMS"


class NotificationStatus(models.TextChoices):
    QUEUED = "QUEUED", "Queued"
    SENT = "SENT", "Sent"
    DELIVERED = "DELIVERED", "Delivered"
    FAILED = "FAILED", "Failed"


class NotificationDelivery(models.Model):
    channel = models.CharField(max_length=16, choices=NotificationChannel.choices)
    provider = models.CharField(max_length=32)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=NotificationStatus.choices, default=NotificationStatus.QUEUED)
    provider_message_id = models.CharField(max_length=255, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    last_error = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["channel", "provider", "status"]),
            models.Index(fields=["provider_message_id"]),
            models.Index(fields=["created_at"]),
        ]

    def mark_sent(self, provider_message_id=""):
        self.status = NotificationStatus.SENT
        self.provider_message_id = provider_message_id or self.provider_message_id
        self.attempts += 1
        self.sent_at = timezone.now()
        self.last_error = ""
        self.save(update_fields=["status", "provider_message_id", "attempts", "sent_at", "last_error", "updated_at"])

    def mark_delivered(self):
        self.status = NotificationStatus.DELIVERED
        now = timezone.now()
        if not self.sent_at:
            self.sent_at = now
        self.delivered_at = now
        self.save(update_fields=["status", "sent_at", "delivered_at", "updated_at"])

    def mark_failed(self, error_message):
        self.status = NotificationStatus.FAILED
        self.attempts += 1
        self.last_error = str(error_message)[:2000]
        self.save(update_fields=["status", "attempts", "last_error", "updated_at"])


class JobRunStatus(models.TextChoices):
    RUNNING = "RUNNING", "Running"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"


class BackupRun(models.Model):
    status = models.CharField(max_length=16, choices=JobRunStatus.choices, default=JobRunStatus.RUNNING)
    backup_file = models.CharField(max_length=512, blank=True)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    backup_size_bytes = models.BigIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "started_at"]),
            models.Index(fields=["started_at"]),
        ]


class RestoreDrillRun(models.Model):
    backup_run = models.ForeignKey(BackupRun, related_name="restore_drills", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=16, choices=JobRunStatus.choices, default=JobRunStatus.RUNNING)
    details = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "started_at"]),
            models.Index(fields=["started_at"]),
        ]
