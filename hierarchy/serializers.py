from rest_framework import serializers

from .models import Office


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ["id", "name", "level", "parent_office", "location_code"]
        read_only_fields = ["id"]
