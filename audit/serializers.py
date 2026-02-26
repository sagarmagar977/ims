from rest_framework import serializers

from .models import InventoryAuditLog


class InventoryAuditLogSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.title", read_only=True)
    item_number = serializers.CharField(source="item.item_number", read_only=True)
    performed_by_name = serializers.SerializerMethodField()

    def get_performed_by_name(self, obj):
        if not obj.performed_by:
            return None
        return obj.performed_by.get_full_name() or obj.performed_by.username

    class Meta:
        model = InventoryAuditLog
        fields = [
            "id",
            "item",
            "item_name",
            "item_number",
            "action_type",
            "performed_by",
            "performed_by_name",
            "before_data",
            "after_data",
            "remarks",
            "attachment",
            "created_at",
        ]
        read_only_fields = ["id", "performed_by", "created_at"]
