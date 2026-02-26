from rest_framework import viewsets

from common.permissions import IMSAccessPermission
from .models import Category, CustomFieldDefinition
from .serializers import CategorySerializer, CustomFieldDefinitionSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    filterset_fields = ["is_consumable"]
    search_fields = ["name"]
    ordering_fields = ["id", "name"]
    ordering = ["id"]
    permission_classes = [IMSAccessPermission]


class CustomFieldDefinitionViewSet(viewsets.ModelViewSet):
    queryset = CustomFieldDefinition.objects.select_related("category").all().order_by("id")
    serializer_class = CustomFieldDefinitionSerializer
    filterset_fields = ["category", "field_type", "required", "is_unique"]
    search_fields = ["label", "category__name"]
    ordering_fields = ["id", "label"]
    ordering = ["id"]
    permission_classes = [IMSAccessPermission]
