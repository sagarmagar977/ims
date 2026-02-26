from django.urls import path

from .views import (
    AssignmentSummaryByOfficeView,
    DashboardSummaryView,
    InventoryReportExportCSVView,
    InventoryReportExportExcelView,
    InventoryReportExportPDFView,
    InventoryReportView,
    LowStockReportView,
    RecentInventoryActivitiesView,
)

urlpatterns = [
    path("reports/dashboard-summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("reports/recent-inventory-activities/", RecentInventoryActivitiesView.as_view(), name="recent-inventory-activities"),
    path("reports/inventory/", InventoryReportView.as_view(), name="inventory-report"),
    path("reports/inventory/export-csv/", InventoryReportExportCSVView.as_view(), name="inventory-report-export-csv"),
    path("reports/inventory/export-excel/", InventoryReportExportExcelView.as_view(), name="inventory-report-export-excel"),
    path("reports/inventory/export-pdf/", InventoryReportExportPDFView.as_view(), name="inventory-report-export-pdf"),
    path("reports/low-stock/", LowStockReportView.as_view(), name="low-stock-report"),
    path(
        "reports/assignment-summary-by-office/",
        AssignmentSummaryByOfficeView.as_view(),
        name="assignment-summary-by-office",
    ),
]
