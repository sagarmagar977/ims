from django.conf import settings
from django.db import models

from inventory.models import InventoryItem


class InventoryActionType(models.TextChoices):
    CREATE = "CREATE", "Create"
    UPDATE = "UPDATE", "Update"
    ASSIGN = "ASSIGN", "Assign"
    RETURN = "RETURN", "Return"
    REPAIR = "REPAIR", "Repair"
    DISPOSE = "DISPOSE", "Dispose"


class InventoryAuditLog(models.Model):
    item = models.ForeignKey(InventoryItem, related_name="audit_logs", on_delete=models.CASCADE)
    action_type = models.CharField(max_length=16, choices=InventoryActionType.choices)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="inventory_audit_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    before_data = models.JSONField(default=dict, blank=True)
    after_data = models.JSONField(default=dict, blank=True)
    remarks = models.TextField(blank=True)
    attachment = models.FileField(upload_to="inventory/audit_attachments/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["item", "created_at"]),
            models.Index(fields=["action_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.item.title} - {self.action_type}"
