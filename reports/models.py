from django.db import models


class ReportType(models.TextChoices):
    INVENTORY_DAILY_SUMMARY = "INVENTORY_DAILY_SUMMARY", "Inventory Daily Summary"


class ReportGenerationStatus(models.TextChoices):
    GENERATING = "GENERATING", "Generating"
    GENERATED = "GENERATED", "Generated"
    FAILED = "FAILED", "Failed"


class GeneratedReport(models.Model):
    report_type = models.CharField(max_length=64, choices=ReportType.choices)
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=16, choices=ReportGenerationStatus.choices, default=ReportGenerationStatus.GENERATING)
    row_count = models.PositiveIntegerField(default=0)
    payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["report_type", "period_start", "period_end"]),
            models.Index(fields=["status", "created_at"]),
        ]
