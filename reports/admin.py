from django.contrib import admin

from .models import GeneratedReport


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ("id", "report_type", "period_start", "period_end", "status", "row_count", "created_at")
    list_filter = ("report_type", "status", "created_at")
    search_fields = ("report_type",)
