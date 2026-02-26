from rest_framework import serializers

from .models import Category, CustomFieldDefinition


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "is_consumable"]
        read_only_fields = ["id"]


class CustomFieldDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomFieldDefinition
        fields = [
            "id",
            "category",
            "label",
            "field_type",
            "required",
            "is_unique",
            "select_options",
        ]
        read_only_fields = ["id"]
