# Chapter 18 — Reports App Files

## Build Roadmap Position
- Stage: Core Domain
- You are here: Chapter 18
- Before this: Chapter 17
- After this: Chapter 19

## Learning Objectives
- Understand report endpoints and aggregated metrics.
- Trace export flows for CSV, Excel, and PDF.
- Validate report behavior from tests.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 18 — Reports App Files

## Learning Goals
- Understand report endpoints and aggregated metrics.
- Trace export flows for CSV, Excel, and PDF.
- Validate report behavior from tests.

## Reference Files
- `reports/views.py`
- `reports/urls.py`
- `reports/models.py`
- `reports/tests.py`
- `reports/admin.py`
- `reports/apps.py`

## File Breakdown

## 1) `reports/views.py`
- `DashboardSummaryView`: counts inventory/assignments/stocks/offices with scoped querysets.
- `LowStockReportView`: returns consumables where `quantity <= min_threshold` and alerts are enabled.
- `AssignmentSummaryByOfficeView`: grouped assignment totals by office.
- `RecentInventoryActivitiesView`: latest 50 audit entries with display payload.
- `InventoryReportView`:
  - filtering by `category`, `status`, `office`, `fiscal_year`.
  - fiscal-year logic uses window `YYYY-07-16` to `YYYY-07-15`.
- Export subclasses:
  - `InventoryReportExportCSVView`
  - `InventoryReportExportExcelView` (openpyxl)
  - `InventoryReportExportPDFView` (reportlab)

## 2) `reports/urls.py`
- Declares report routes under `reports/*`:
  - dashboard summary
  - recent activities
  - inventory list
  - inventory CSV/Excel/PDF exports
  - low stock
  - assignment summary by office

## 3) `reports/models.py`
- No report model is defined in current file (placeholder only).

## 4) `reports/tests.py`
- `ReportExportTests` verifies:
  - Excel endpoint content type and XLSX signature (`PK`).
  - PDF endpoint content type and PDF signature (`%PDF`).
  - `/api/v1/reports/inventory/` works.

## 5) Other files
- `reports/admin.py` currently has no model registrations.
- `reports/apps.py` defines `ReportsConfig`.

## Chapter 18 Outcome
You now understand how report APIs aggregate scoped data and how export formats are generated directly from the same filtered inventory queryset.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
### File: `reports/views.py`
```python
from django.db.models import Count, F, Q
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from actions.models import AssignmentStatus, ItemAssignment
from audit.models import InventoryAuditLog
from common.access import scope_queryset_by_user
from hierarchy.models import Office
from inventory.models import ConsumableStock, FixedAsset, InventoryItem, InventoryStatus


class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        item_qs = scope_queryset_by_user(InventoryItem.objects.all(), request.user, "office_id")
        assignment_qs = scope_queryset_by_user(ItemAssignment.objects.all(), request.user, "item__office_id")
        stock_qs = scope_queryset_by_user(ConsumableStock.objects.all(), request.user, "item__office_id")
        fixed_qs = scope_queryset_by_user(FixedAsset.objects.all(), request.user, "item__office_id")
        office_ids = item_qs.values_list("office_id", flat=True).distinct()
        assigned_count = assignment_qs.filter(status=AssignmentStatus.ASSIGNED).values("item_id").distinct().count()
        unassigned_count = max(item_qs.count() - assigned_count, 0)
        data = {
            "total_inventory_items": item_qs.count(),
            "active_inventory_items": item_qs.filter(status=InventoryStatus.ACTIVE).count(),
            "disposed_inventory_items": item_qs.filter(status=InventoryStatus.DISPOSED).count(),
            "fixed_assets": fixed_qs.count(),
            "consumable_stocks": stock_qs.count(),
            "active_assignments": assignment_qs.filter(status=AssignmentStatus.ASSIGNED).count(),
            "returned_assignments": assignment_qs.filter(status=AssignmentStatus.RETURNED).count(),
            "low_stock_items": stock_qs.filter(
                reorder_alert_enabled=True,
                quantity__lte=F("min_threshold"),
            ).count(),
            "assigned_assets": assigned_count,
            "unassigned_assets": unassigned_count,
            "active_offices": Office.objects.filter(id__in=office_ids).count(),
        }
        return Response(data)


class LowStockReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stocks_qs = scope_queryset_by_user(ConsumableStock.objects.all(), request.user, "item__office_id")
        stocks = (
            stocks_qs.select_related("item", "item__office", "item__category")
            .filter(reorder_alert_enabled=True, quantity__lte=F("min_threshold"))
            .order_by("quantity", "id")
        )

        data = [
            {
                "stock_id": stock.id,
                "item_id": stock.item_id,
                "title": stock.item.title,
                "office": stock.item.office.name,
                "category": stock.item.category.name,
                "quantity": stock.quantity,
                "min_threshold": stock.min_threshold,
                "unit": stock.unit,
            }
            for stock in stocks
        ]
        return Response(data)


class AssignmentSummaryByOfficeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        scoped_qs = scope_queryset_by_user(ItemAssignment.objects.all(), request.user, "item__office_id")
        data = list(
            scoped_qs.values("item__office__id", "item__office__name")
            .annotate(
                total=Count("id"),
                active=Count("id", filter=Q(status=AssignmentStatus.ASSIGNED)),
                returned=Count("id", filter=Q(status=AssignmentStatus.RETURNED)),
            )
            .order_by("item__office__name")
        )
        return Response(data)


class RecentInventoryActivitiesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        logs_qs = scope_queryset_by_user(InventoryAuditLog.objects.all(), request.user, "item__office_id")
        logs = (
            logs_qs.select_related("item", "performed_by")
            .all()
            .order_by("-created_at")[:50]
        )
        data = [
            {
                "id": log.id,
                "item_name": log.item.title,
                "unique_number": log.item.item_number,
                "performed_by": (log.performed_by.get_full_name() or log.performed_by.username) if log.performed_by else None,
                "date": log.created_at.date(),
                "amount": str(log.item.amount),
                "status": log.action_type,
                "action": log.remarks,
            }
            for log in logs
        ]
        return Response(data)


class InventoryReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self, request):
        queryset = scope_queryset_by_user(InventoryItem.objects.all(), request.user, "office_id").select_related("category", "office").order_by("-created_at")
        category = request.query_params.get("category")
        status = request.query_params.get("status")
        office = request.query_params.get("office")
        fiscal_year = request.query_params.get("fiscal_year")

        if category:
            queryset = queryset.filter(category_id=category)
        if status:
            queryset = queryset.filter(status=status)
        if office:
            queryset = queryset.filter(office_id=office)

        # Fiscal year format: YYYY-YYYY, window from Jul 16 first year to Jul 15 second year.
        if fiscal_year and "-" in fiscal_year:
            start_year, end_year = fiscal_year.split("-", 1)
            if start_year.isdigit() and end_year.isdigit():
                queryset = queryset.filter(
                    purchased_date__gte=f"{start_year}-07-16",
                    purchased_date__lte=f"{end_year}-07-15",
                )

        return queryset

    def get(self, request):
        queryset = self.get_queryset(request)
        data = self.serialize_items(queryset)
        return Response(data)

    @staticmethod
    def serialize_items(queryset):
        return [
            {
                "id": item.id,
                "item_name": item.title,
                "item_number": item.item_number,
                "item_type": item.item_type,
                "category": item.category.name,
                "office": item.office.name,
                "status": item.status,
                "amount": str(item.amount),
                "purchased_date": item.purchased_date,
            }
            for item in queryset
        ]


class InventoryReportExportCSVView(InventoryReportView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = self.get_queryset(request)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="inventory_report.csv"'
        response.write("item_name,item_number,item_type,category,office,status,amount,purchased_date\n")
        for item in queryset:
            response.write(
                f'"{item.title}","{item.item_number or ""}","{item.item_type}","{item.category.name}","{item.office.name}","{item.status}","{item.amount}","{item.purchased_date or ""}"\n'
            )
        return response


class InventoryReportExportExcelView(InventoryReportView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = self.get_queryset(request)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Inventory Report"

        headers = ["Item Name", "Item Number", "Item Type", "Category", "Office", "Status", "Amount", "Purchased Date"]
        sheet.append(headers)

        for item in queryset:
            sheet.append(
                [
                    item.title,
                    item.item_number or "",
                    item.item_type,
                    item.category.name,
                    item.office.name,
                    item.status,
                    float(item.amount),
                    item.purchased_date.isoformat() if item.purchased_date else "",
                ]
            )

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="inventory_report.xlsx"'
        workbook.save(response)
        return response


class InventoryReportExportPDFView(InventoryReportView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = self.get_queryset(request)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="inventory_report.pdf"'

        pdf = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        y = height - 40

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, "DoNIDCR - Inventory Report")
        y -= 20

        pdf.setFont("Helvetica", 9)
        pdf.drawString(40, y, "Item Name")
        pdf.drawString(210, y, "Item Number")
        pdf.drawString(300, y, "Category")
        pdf.drawString(390, y, "Office")
        pdf.drawString(480, y, "Status")
        y -= 14

        for item in queryset:
            if y < 50:
                pdf.showPage()
                y = height - 40
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(40, y, "DoNIDCR - Inventory Report (cont.)")
                y -= 20
                pdf.setFont("Helvetica", 9)

            pdf.drawString(40, y, (item.title or "")[:28])
            pdf.drawString(210, y, (item.item_number or "")[:14])
            pdf.drawString(300, y, (item.category.name or "")[:14])
            pdf.drawString(390, y, (item.office.name or "")[:14])
            pdf.drawString(480, y, (item.status or "")[:10])
            y -= 14

        pdf.save()
        return response

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `reports/urls.py`
```python
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

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `reports/models.py`
```python
from django.db import models

# Create your models here.

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `reports/tests.py`
```python
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category
from hierarchy.models import Office, OfficeLevels
from inventory.models import InventoryItem, InventoryItemType
from users.models import User


class ReportExportTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username="admin", password="admin123", email="admin@example.com")
        office = Office.objects.create(name="Central", level=OfficeLevels.CENTRAL, location_code="CENTRAL-1")
        category = Category.objects.create(name="Laptop", is_consumable=False)
        InventoryItem.objects.create(
            category=category,
            office=office,
            title="Laptop A",
            item_number="ITM-100",
            item_type=InventoryItemType.FIXED_ASSET,
            status="ACTIVE",
        )
        self.client.force_authenticate(user=self.user)

    def test_inventory_export_excel(self):
        response = self.client.get("/api/reports/inventory/export-excel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertTrue(response.content.startswith(b"PK"))

    def test_inventory_export_pdf(self):
        response = self.client.get("/api/reports/inventory/export-pdf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_v1_inventory_report_endpoint(self):
        response = self.client.get("/api/v1/reports/inventory/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `reports/admin.py`
```python
from django.contrib import admin

# Register your models here.

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `reports/apps.py`
```python
from django.apps import AppConfig


class ReportsConfig(AppConfig):
    name = 'reports'

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

## Rebuild Step (Hands-on Roadmap)
- Implement or review the files listed in this chapter only.
- Validate behavior discussed in the original chapter explanation.
- Confirm readiness for the next chapter transition.

## Chapter Summary
This chapter ties repository explanation to exact code references and prepares the next build step.

## Files Used
- `reports/views.py`
- `reports/urls.py`
- `reports/models.py`
- `reports/tests.py`
- `reports/admin.py`
- `reports/apps.py`

