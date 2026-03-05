import csv
import io

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.models import InventoryActionType
from audit.utils import create_inventory_audit_log
from common.access import scope_queryset_by_user
from common.permissions import IMSAccessPermission
from .models import AssignmentStatus, ItemAssignment
from .serializers import ItemAssignmentSerializer


class ItemAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ItemAssignment.objects.select_related(
        "item",
        "assigned_to_user",
        "assigned_to_office",
        "assigned_by",
    ).all().order_by("id")
    serializer_class = ItemAssignmentSerializer
    filterset_fields = ["item", "assigned_to_user", "assigned_to_office", "status", "assign_till"]
    search_fields = ["item__title", "item__item_number", "assigned_to_user__username", "assigned_to_office__name", "remarks"]
    ordering_fields = ["id", "handover_date", "assign_till", "created_at", "returned_at"]
    ordering = ["-created_at"]
    permission_classes = [IMSAccessPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        return scope_queryset_by_user(queryset, self.request.user, "item__office_id")

    def perform_create(self, serializer):
        assignment = serializer.save(assigned_by=self.request.user)
        create_inventory_audit_log(
            item=assignment.item,
            action_type=InventoryActionType.ASSIGN,
            user=self.request.user,
            after_data={
                "assignment_id": assignment.id,
                "assigned_to_user": assignment.assigned_to_user_id,
                "assigned_to_office": assignment.assigned_to_office_id,
                "status": assignment.status,
                "assign_till": assignment.assign_till.isoformat() if assignment.assign_till else None,
            },
            remarks="Item assigned",
        )

    def perform_update(self, serializer):
        before_instance = self.get_object()
        before = {
            "status": before_instance.status,
            "assigned_to_user": before_instance.assigned_to_user_id,
            "assigned_to_office": before_instance.assigned_to_office_id,
            "returned_at": before_instance.returned_at.isoformat() if before_instance.returned_at else None,
        }
        assignment = serializer.save()
        action_type = InventoryActionType.RETURN if assignment.status == AssignmentStatus.RETURNED else InventoryActionType.ASSIGN
        create_inventory_audit_log(
            item=assignment.item,
            action_type=action_type,
            user=self.request.user,
            before_data=before,
            after_data={
                "status": assignment.status,
                "assigned_to_user": assignment.assigned_to_user_id,
                "assigned_to_office": assignment.assigned_to_office_id,
                "returned_at": assignment.returned_at.isoformat() if assignment.returned_at else None,
            },
            remarks="Item assignment updated",
        )

    @action(detail=False, methods=["get"], url_path="summary-by-assignee")
    def summary_by_assignee(self, request):
        today = timezone.now().date()
        scoped_qs = scope_queryset_by_user(ItemAssignment.objects.all(), request.user, "item__office_id")
        data = list(
            scoped_qs.values(
                "assigned_to_user",
                "assigned_to_user__first_name",
                "assigned_to_user__last_name",
                "assigned_to_user__username",
                "assigned_to_office",
                "assigned_to_office__name",
            )
            .annotate(
                total_items=Count("id"),
                active=Count("id", filter=Q(status=AssignmentStatus.ASSIGNED)),
                overdue=Count(
                    "id",
                    filter=Q(status=AssignmentStatus.ASSIGNED, assign_till__lt=today),
                ),
                returned=Count("id", filter=Q(status=AssignmentStatus.RETURNED)),
            )
            .order_by("assigned_to_user__username", "assigned_to_office__name")
        )
        return Response(data)

    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

        decoded = file_obj.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))
        created_count = 0
        errors = []

        for index, row in enumerate(reader, start=2):
            payload = {
                "item": row.get("item"),
                "assigned_to_user": row.get("assigned_to_user") or None,
                "assigned_to_office": row.get("assigned_to_office") or None,
                "handover_date": row.get("handover_date"),
                "assign_till": row.get("assign_till") or None,
                "handover_condition": row.get("handover_condition") or "GOOD",
                "status": row.get("status") or "ASSIGNED",
                "remarks": row.get("remarks") or "",
            }
            serializer = self.get_serializer(data=payload)
            if serializer.is_valid():
                assignment = serializer.save(assigned_by=request.user)
                create_inventory_audit_log(
                    item=assignment.item,
                    action_type=InventoryActionType.ASSIGN,
                    user=request.user,
                    after_data={
                        "assignment_id": assignment.id,
                        "assigned_to_user": assignment.assigned_to_user_id,
                        "assigned_to_office": assignment.assigned_to_office_id,
                        "status": assignment.status,
                        "assign_till": assignment.assign_till.isoformat() if assignment.assign_till else None,
                    },
                    remarks="Item assigned (bulk import)",
                )
                created_count += 1
            else:
                errors.append({"line": index, "errors": serializer.errors})

        return Response(
            {"created": created_count, "failed": len(errors), "errors": errors},
            status=status.HTTP_200_OK,
        )
