from rest_framework import viewsets
from rest_framework.permissions import AllowAny, BasePermission, IsAdminUser, IsAuthenticated

from .models import User
from .serializers import UserSerializer


class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated and (request.user.is_staff or obj.pk == request.user.pk))


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    filterset_fields = ["role", "office", "is_active"]
    search_fields = ["username", "first_name", "last_name", "full_name_nepali", "email", "office__name"]
    ordering_fields = ["id", "username", "date_joined"]
    ordering = ["id"]

    def get_permissions(self):
        if self.action == "create":
            if not User.objects.exists():
                return [AllowAny()]
            return [IsAdminUser()]
        if self.action in ["list", "destroy"]:
            return [IsAdminUser()]
        if self.action in ["retrieve", "update", "partial_update"]:
            return [IsAuthenticated(), IsSelfOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(pk=self.request.user.pk)

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()
