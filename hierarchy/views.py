from rest_framework import viewsets

from common.access import scope_queryset_by_user
from common.permissions import IMSAccessPermission
from .models import Office
from .serializers import OfficeSerializer


class OfficeViewSet(viewsets.ModelViewSet):
    queryset = Office.objects.select_related("parent_office").all().order_by("id")
    serializer_class = OfficeSerializer
    filterset_fields = ["level", "parent_office"]
    search_fields = ["name", "location_code"]
    ordering_fields = ["id", "name", "location_code"]
    ordering = ["id"]
    permission_classes = [IMSAccessPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        return scope_queryset_by_user(queryset, self.request.user, "id")
