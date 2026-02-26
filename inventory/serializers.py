from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from actions.models import AssignmentStatus
from .models import (
    ConsumableStock,
    ConsumableStockTransaction,
    FixedAsset,
    InventoryItem,
    InventoryItemType,
    StockTransactionType,
)


class InventoryItemSerializer(serializers.ModelSerializer):
    serial_number = serializers.SerializerMethodField()
    assigned_to = serializers.SerializerMethodField()
    assignment_status = serializers.SerializerMethodField()

    class Meta:
        model = InventoryItem
        fields = [
            "id",
            "category",
            "office",
            "title",
            "item_number",
            "item_type",
            "status",
            "image",
            "amount",
            "price",
            "currency",
            "store",
            "project",
            "department",
            "manufacturer",
            "purchased_date",
            "pi_document",
            "warranty_document",
            "description",
            "dynamic_data",
            "serial_number",
            "assigned_to",
            "assignment_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "serial_number", "assigned_to", "assignment_status", "created_at", "updated_at"]

    def validate(self, attrs):
        category = attrs.get("category", getattr(self.instance, "category", None))
        item_type = attrs.get("item_type", getattr(self.instance, "item_type", None))
        if category and item_type:
            if category.is_consumable and item_type == InventoryItemType.FIXED_ASSET:
                raise serializers.ValidationError({"item_type": "Consumable category requires CONSUMABLE item type."})
            if not category.is_consumable and item_type == InventoryItemType.CONSUMABLE:
                raise serializers.ValidationError({"item_type": "Non-consumable category requires FIXED_ASSET item type."})
        return attrs

    def get_serial_number(self, obj):
        fixed_asset = getattr(obj, "fixed_asset", None)
        return getattr(fixed_asset, "serial_number", None)

    def get_assigned_to(self, obj):
        active_assignment = obj.assignments.filter(status=AssignmentStatus.ASSIGNED).select_related(
            "assigned_to_user", "assigned_to_office"
        ).first()
        if not active_assignment:
            return None
        if active_assignment.assigned_to_user:
            return active_assignment.assigned_to_user.get_full_name() or active_assignment.assigned_to_user.username
        if active_assignment.assigned_to_office:
            return active_assignment.assigned_to_office.name
        return None

    def get_assignment_status(self, obj):
        has_active = obj.assignments.filter(status=AssignmentStatus.ASSIGNED).exists()
        return "ASSIGNED" if has_active else "UNASSIGNED"


class FixedAssetSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        item = attrs.get("item", getattr(self.instance, "item", None))
        if item is None:
            return attrs

        if item.category.is_consumable:
            raise serializers.ValidationError({"item": "Consumable category cannot have FixedAsset subtype."})

        if hasattr(item, "consumable_stock"):
            raise serializers.ValidationError({"item": "InventoryItem cannot be both FixedAsset and ConsumableStock."})
        return attrs

    class Meta:
        model = FixedAsset
        fields = [
            "id",
            "item",
            "asset_tag",
            "serial_number",
            "purchase_date",
            "warranty_expiry_date",
            "invoice_file",
        ]
        read_only_fields = ["id"]


class ConsumableStockSerializer(serializers.ModelSerializer):
    stock_status = serializers.SerializerMethodField()

    def validate(self, attrs):
        item = attrs.get("item", getattr(self.instance, "item", None))
        if item is None:
            return attrs

        if not item.category.is_consumable:
            raise serializers.ValidationError({"item": "Non-consumable category cannot have ConsumableStock subtype."})

        if hasattr(item, "fixed_asset"):
            raise serializers.ValidationError({"item": "InventoryItem cannot be both FixedAsset and ConsumableStock."})
        return attrs

    class Meta:
        model = ConsumableStock
        fields = [
            "id",
            "item",
            "initial_quantity",
            "quantity",
            "min_threshold",
            "reorder_alert_enabled",
            "unit",
            "stock_status",
        ]
        read_only_fields = ["id", "stock_status"]

    def get_stock_status(self, obj):
        if obj.quantity <= 0:
            return "OUT_OF_STOCK"
        if obj.quantity <= obj.min_threshold:
            return "LOW_STOCK"
        return "ON_BOARDED"


class ConsumableStockTransactionSerializer(serializers.ModelSerializer):
    item_name = serializers.SerializerMethodField()
    item_number = serializers.SerializerMethodField()
    performed_by_name = serializers.SerializerMethodField()

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        stock = validated_data["stock"]
        transaction_type = validated_data["transaction_type"]
        quantity = validated_data["quantity"]

        if transaction_type in [StockTransactionType.STOCK_OUT, StockTransactionType.DAMAGE]:
            if stock.quantity < quantity:
                raise serializers.ValidationError({"quantity": "Insufficient stock for this transaction."})
            new_balance = Decimal(stock.quantity) - Decimal(quantity)
        else:
            new_balance = Decimal(stock.quantity) + Decimal(quantity)

        stock.quantity = new_balance
        stock.save(update_fields=["quantity"])

        validated_data["balance_after"] = new_balance
        return super().create(validated_data)

    class Meta:
        model = ConsumableStockTransaction
        fields = [
            "id",
            "stock",
            "transaction_type",
            "quantity",
            "balance_after",
            "status",
            "amount",
            "assigned_to",
            "department",
            "description",
            "image",
            "performed_by",
            "item_name",
            "item_number",
            "performed_by_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "balance_after",
            "performed_by",
            "item_name",
            "item_number",
            "performed_by_name",
            "created_at",
        ]

    def get_item_name(self, obj):
        return obj.stock.item.title

    def get_item_number(self, obj):
        return obj.stock.item.item_number

    def get_performed_by_name(self, obj):
        if not obj.performed_by:
            return None
        return obj.performed_by.get_full_name() or obj.performed_by.username
