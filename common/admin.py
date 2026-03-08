from django.contrib import admin

from .models import BackupRun, NotificationDelivery, RestoreDrillRun


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ("id", "channel", "provider", "recipient", "status", "provider_message_id", "created_at")
    search_fields = ("recipient", "provider_message_id", "subject")
    list_filter = ("channel", "provider", "status", "created_at")


@admin.register(BackupRun)
class BackupRunAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "backup_file", "backup_size_bytes", "started_at", "finished_at")
    list_filter = ("status", "started_at")
    search_fields = ("backup_file", "checksum_sha256")


@admin.register(RestoreDrillRun)
class RestoreDrillRunAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "backup_run", "started_at", "finished_at")
    list_filter = ("status", "started_at")
