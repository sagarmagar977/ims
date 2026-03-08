from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import F
from django.utils import timezone

from common.models import BackupRun, JobRunStatus, NotificationDelivery, NotificationStatus, RestoreDrillRun
from inventory.models import ConsumableStock
from reports.models import GeneratedReport, ReportGenerationStatus


def current_operational_metrics():
    now = timezone.now()
    one_day_ago = now - timedelta(hours=24)
    backup = BackupRun.objects.filter(status=JobRunStatus.SUCCESS).order_by("-finished_at").first()
    drill = RestoreDrillRun.objects.order_by("-finished_at", "-started_at").first()
    failed_notifications_24h = NotificationDelivery.objects.filter(
        status=NotificationStatus.FAILED,
        created_at__gte=one_day_ago,
    ).count()
    low_stock_count = ConsumableStock.objects.filter(quantity__lte=F("min_threshold"), reorder_alert_enabled=True).count()
    reports_generated_24h = GeneratedReport.objects.filter(
        status=ReportGenerationStatus.GENERATED,
        created_at__gte=one_day_ago,
    ).count()

    return {
        "timestamp": now.isoformat(),
        "failed_notifications_24h": failed_notifications_24h,
        "low_stock_count": low_stock_count,
        "reports_generated_24h": reports_generated_24h,
        "latest_backup": {
            "id": getattr(backup, "id", None),
            "status": getattr(backup, "status", None),
            "finished_at": backup.finished_at.isoformat() if backup and backup.finished_at else None,
        },
        "latest_restore_drill": {
            "id": getattr(drill, "id", None),
            "status": getattr(drill, "status", None),
            "finished_at": drill.finished_at.isoformat() if drill and drill.finished_at else None,
        },
    }


def evaluate_slo_breaches(metrics=None):
    if metrics is None:
        metrics = current_operational_metrics()
    now = timezone.now()
    breaches = []

    max_backup_age_hours = int(getattr(settings, "SLO_BACKUP_MAX_AGE_HOURS", 24))
    max_failed_notifications_24h = int(getattr(settings, "SLO_MAX_FAILED_NOTIFICATIONS_24H", 10))
    require_successful_restore_drill = str(getattr(settings, "SLO_REQUIRE_SUCCESSFUL_RESTORE_DRILL", "1")).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    restore_drill_max_age_days = int(getattr(settings, "SLO_RESTORE_DRILL_MAX_AGE_DAYS", 14))

    backup_finished_at = metrics.get("latest_backup", {}).get("finished_at")
    if not backup_finished_at:
        breaches.append("No successful backup found.")
    else:
        backup_dt = datetime.fromisoformat(backup_finished_at)
        if now - backup_dt > timedelta(hours=max_backup_age_hours):
            breaches.append(f"Latest successful backup older than {max_backup_age_hours}h.")

    if metrics.get("failed_notifications_24h", 0) > max_failed_notifications_24h:
        breaches.append(
            f"Failed notifications in last 24h exceeded threshold ({max_failed_notifications_24h})."
        )

    if require_successful_restore_drill:
        drill = RestoreDrillRun.objects.filter(status=JobRunStatus.SUCCESS).order_by("-finished_at").first()
        if drill is None or not drill.finished_at:
            breaches.append("No successful restore drill found.")
        elif now - drill.finished_at > timedelta(days=restore_drill_max_age_days):
            breaches.append(f"Latest successful restore drill older than {restore_drill_max_age_days} days.")

    return breaches
