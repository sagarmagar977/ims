from celery import shared_task
from django.conf import settings
from django.db.models import F
from django.utils import timezone

from inventory.models import ConsumableStock, InventoryItem
from reports.models import GeneratedReport, ReportGenerationStatus, ReportType

from .backups import create_database_backup, run_restore_drill
from .notifications import send_email_notification, send_low_stock_alert_for_stock
from .observability import current_operational_metrics, evaluate_slo_breaches


@shared_task
def periodic_low_stock_alerts():
    low_stocks = (
        ConsumableStock.objects.select_related("item", "item__office")
        .filter(reorder_alert_enabled=True, quantity__lte=F("min_threshold"))
        .order_by("id")
    )
    sent_count = 0
    for stock in low_stocks:
        deliveries = send_low_stock_alert_for_stock(stock, trigger="periodic_scheduler")
        sent_count += len(deliveries)
    return {"low_stock_items": low_stocks.count(), "deliveries_attempted": sent_count}


@shared_task
def periodic_inventory_report_generation():
    today = timezone.now().date()
    report = GeneratedReport.objects.create(
        report_type=ReportType.INVENTORY_DAILY_SUMMARY,
        period_start=today,
        period_end=today,
        status=ReportGenerationStatus.GENERATING,
    )

    summary = {
        "total_inventory_items": InventoryItem.objects.count(),
        "low_stock_items": ConsumableStock.objects.filter(
            reorder_alert_enabled=True,
            quantity__lte=F("min_threshold"),
        ).count(),
    }
    report.payload = summary
    report.row_count = summary["total_inventory_items"]
    report.status = ReportGenerationStatus.GENERATED
    report.save(update_fields=["payload", "row_count", "status", "updated_at"])

    recipients = [email for email in getattr(settings, "PERIODIC_REPORT_EMAILS", []) if email]
    if recipients:
        send_email_notification(
            subject=f"IMS Daily Inventory Summary ({today.isoformat()})",
            body=(
                f"Report ID: {report.id}\n"
                f"Total inventory items: {summary['total_inventory_items']}\n"
                f"Low stock items: {summary['low_stock_items']}\n"
            ),
            recipients=recipients,
            metadata={"event": "periodic_inventory_report", "report_id": report.id},
        )

    return {"report_id": report.id, **summary}


@shared_task
def periodic_database_backup():
    run = create_database_backup()
    return {
        "backup_run_id": run.id,
        "status": run.status,
        "backup_file": run.backup_file,
        "size_bytes": run.backup_size_bytes,
    }


@shared_task
def periodic_restore_drill():
    drill = run_restore_drill()
    return {
        "restore_drill_id": drill.id,
        "status": drill.status,
        "backup_run_id": drill.backup_run_id,
    }


@shared_task
def periodic_slo_monitor():
    metrics = current_operational_metrics()
    breaches = evaluate_slo_breaches(metrics=metrics)
    recipients = [email for email in getattr(settings, "OPS_ALERT_EMAILS", []) if email]
    if breaches and recipients:
        send_email_notification(
            subject="IMS SLO Alert",
            body="\n".join(["SLO breach detected:"] + [f"- {b}" for b in breaches]),
            recipients=recipients,
            metadata={"event": "slo_breach", "breaches": breaches, "metrics": metrics},
        )
    return {"breaches": breaches, "metrics": metrics}
