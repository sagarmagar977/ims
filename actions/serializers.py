from rest_framework import serializers

from .models import AssignmentStatus, ItemAssignment


class ItemAssignmentSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.title", read_only=True)
    item_number = serializers.CharField(source="item.item_number", read_only=True)

    def validate(self, attrs):
        status = attrs.get("status", getattr(self.instance, "status", None))
        returned_at = attrs.get("returned_at", getattr(self.instance, "returned_at", None))
        assigned_to_user = attrs.get("assigned_to_user", getattr(self.instance, "assigned_to_user", None))
        assigned_to_office = attrs.get("assigned_to_office", getattr(self.instance, "assigned_to_office", None))

        if not assigned_to_user and not assigned_to_office:
            raise serializers.ValidationError({"non_field_errors": ["Assignment must target a user or an office."]})
        if status == AssignmentStatus.RETURNED and not returned_at:
            raise serializers.ValidationError({"returned_at": "Returned assignment must include returned_at."})
        return attrs

    class Meta:
        model = ItemAssignment
        fields = [
            "id",
            "item",
            "assigned_to_user",
            "assigned_to_office",
            "assigned_by",
            "handover_date",
            "assign_till",
            "handover_condition",
            "handover_letter",
            "status",
            "returned_at",
            "return_condition",
            "damage_photo",
            "remarks",
            "item_name",
            "item_number",
            "created_at",
        ]
        read_only_fields = ["id", "assigned_by", "created_at"]
