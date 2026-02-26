from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models

from catalog.models import Category
from hierarchy.models import Office


class InventoryStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    DISPOSED = "DISPOSED", "Disposed"
    ASSIGNED = "ASSIGNED", "Assigned"
    UNASSIGNED = "UNASSIGNED", "Unassigned"


class InventoryItemType(models.TextChoices):
    FIXED_ASSET = "FIXED_ASSET", "Fixed Asset"
    CONSUMABLE = "CONSUMABLE", "Consumable"


class InventoryItem(models.Model):
    category = models.ForeignKey(Category, related_name="items", on_delete=models.PROTECT)
    office = models.ForeignKey(Office, related_name="items", on_delete=models.PROTECT)

    title = models.CharField(max_length=255)
    item_number = models.CharField(max_length=64, unique=True, null=True, blank=True)
    item_type = models.CharField(max_length=16, choices=InventoryItemType.choices, default=InventoryItemType.FIXED_ASSET)
    status = models.CharField(max_length=16, choices=InventoryStatus.choices, default=InventoryStatus.ACTIVE)
    image = models.FileField(upload_to="inventory/images/", null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=16, blank=True)
    store = models.CharField(max_length=128, blank=True)
    project = models.CharField(max_length=128, blank=True)
    department = models.CharField(max_length=128, blank=True)
    manufacturer = models.CharField(max_length=128, blank=True)
    purchased_date = models.DateField(null=True, blank=True)
    pi_document = models.FileField(upload_to="inventory/pi_documents/", null=True, blank=True)
    warranty_document = models.FileField(upload_to="inventory/warranty_documents/", null=True, blank=True)
    description = models.TextField(blank=True)
    dynamic_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["category", "office"]),
            models.Index(fields=["status"]),
            models.Index(fields=["item_number"]),
        ]

    def clean(self):
        super().clean()

        if self.pk:
            has_fixed = hasattr(self, "fixed_asset")
            has_consumable = hasattr(self, "consumable_stock")

            if has_fixed and has_consumable:
                raise ValidationError("InventoryItem cannot be both FixedAsset and ConsumableStock.")

            if self.category_id:
                if self.category.is_consumable and has_fixed:
                    raise ValidationError("Consumable category cannot have FixedAsset subtype.")
                if not self.category.is_consumable and has_consumable:
                    raise ValidationError("Non-consumable category cannot have ConsumableStock subtype.")

    def __str__(self) -> str:
        return f"{self.title} @ {self.office}"


class FixedAsset(models.Model):
    item = models.OneToOneField(
        InventoryItem,
        related_name="fixed_asset",
        on_delete=models.CASCADE,
    )
    asset_tag = models.CharField(max_length=64, blank=True)
    serial_number = models.CharField(max_length=128, unique=True, null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    warranty_expiry_date = models.DateField(null=True, blank=True)
    invoice_file = models.FileField(upload_to="inventory/invoices/", null=True, blank=True)

    def __str__(self) -> str:
        return f"FixedAsset: {self.item.title}"


class ConsumableStock(models.Model):
    item = models.OneToOneField(
        InventoryItem,
        related_name="consumable_stock",
        on_delete=models.CASCADE,
    )
    initial_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    min_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_alert_enabled = models.BooleanField(default=True)
    unit = models.CharField(max_length=32, default="pcs")

    def __str__(self) -> str:
        return f"ConsumableStock: {self.item.title} ({self.quantity} {self.unit})"


class StockTransactionType(models.TextChoices):
    STOCK_IN = "STOCK_IN", "Stock In"
    STOCK_OUT = "STOCK_OUT", "Stock Out"
    DAMAGE = "DAMAGE", "Damage"
    ADJUSTMENT = "ADJUSTMENT", "Adjustment"


class ConsumableStockTransaction(models.Model):
    stock = models.ForeignKey(ConsumableStock, related_name="transactions", on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=16, choices=StockTransactionType.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=32, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="stock_transactions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    department = models.CharField(max_length=128, blank=True)
    description = models.TextField(blank=True)
    image = models.FileField(upload_to="inventory/stock_transactions/", null=True, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="performed_stock_transactions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["stock", "created_at"]),
            models.Index(fields=["transaction_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.stock.item.title} - {self.transaction_type} ({self.quantity})"
