from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from hierarchy.models import Office
from inventory.models import InventoryItem


class AssignmentStatus(models.TextChoices):
    ASSIGNED = "ASSIGNED", "Assigned"
    RETURNED = "RETURNED", "Returned"


class ItemCondition(models.TextChoices):
    GOOD = "GOOD", "Good"
    FAIR = "FAIR", "Fair"
    DAMAGED = "DAMAGED", "Damaged"


class ItemAssignment(models.Model):
    item = models.ForeignKey(InventoryItem, related_name="assignments", on_delete=models.CASCADE)
    assigned_to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="item_assignments",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    assigned_to_office = models.ForeignKey(
        Office,
        related_name="item_assignments",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="assigned_items",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    handover_date = models.DateField()
    assign_till = models.DateField(null=True, blank=True)
    handover_condition = models.CharField(max_length=16, choices=ItemCondition.choices, default=ItemCondition.GOOD)
    handover_letter = models.FileField(upload_to="inventory/handover_letters/", null=True, blank=True)
    status = models.CharField(max_length=16, choices=AssignmentStatus.choices, default=AssignmentStatus.ASSIGNED)
    returned_at = models.DateTimeField(null=True, blank=True)
    return_condition = models.CharField(max_length=16, choices=ItemCondition.choices, null=True, blank=True)
    damage_photo = models.FileField(upload_to="inventory/damage_photos/", null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(Q(assigned_to_user__isnull=False) | Q(assigned_to_office__isnull=False)),
                name="item_assignment_target_required",
            ),
            models.UniqueConstraint(
                fields=["item"],
                condition=Q(status=AssignmentStatus.ASSIGNED),
                name="uniq_active_assignment_per_item",
            ),
        ]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["handover_date"]),
        ]

    def clean(self):
        super().clean()
        if not self.assigned_to_user_id and not self.assigned_to_office_id:
            raise ValidationError("Assignment must target a user or an office.")
        if self.status == AssignmentStatus.RETURNED and not self.returned_at:
            raise ValidationError("Returned assignment must include returned_at.")

    def __str__(self) -> str:
        return f"{self.item.title} - {self.status}"
