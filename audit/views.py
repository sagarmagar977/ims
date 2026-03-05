from rest_framework import viewsets

from common.access import scope_queryset_by_user
from common.permissions import IMSAccessPermission
from .models import InventoryAuditLog
from .serializers import InventoryAuditLogSerializer


class InventoryAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventoryAuditLog.objects.select_related("item", "performed_by").all().order_by("id")
    serializer_class = InventoryAuditLogSerializer
    filterset_fields = ["item", "action_type", "performed_by"]
    search_fields = ["item__title", "remarks", "performed_by__username"]
    ordering_fields = ["id", "created_at"]
    ordering = ["-created_at"]
    permission_classes = [IMSAccessPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        return scope_queryset_by_user(queryset, self.request.user, "item__office_id")
