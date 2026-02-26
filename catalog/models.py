
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_consumable = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name


class CustomFieldType(models.TextChoices):
    TEXT = "TEXT", "Text"
    NUMBER = "NUMBER", "Number"
    DATE = "DATE", "Date"
    BOOLEAN = "BOOLEAN", "Boolean"
    SELECT = "SELECT", "Select"
    FILE = "FILE", "File"


class CustomFieldDefinition(models.Model):
    category = models.ForeignKey(
        Category,
        related_name="custom_fields",
        on_delete=models.CASCADE,
    )
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=16, choices=CustomFieldType.choices)
    required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    select_options = models.JSONField(default=list, blank=True)

    class Meta:
        # "unique" per category is usually what you want:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "label"],
                name="uniq_custom_field_label_per_category",
            )
        ]
        indexes = [
            models.Index(fields=["category", "field_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.category.name}: {self.label}"
