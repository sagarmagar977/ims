from django.db import models

# Create your models here.
class OfficeLevels(models.TextChoices):
    CENTRAL ="CENTRAL","central"
    PROVINCIAL = "PROVINCIAL","provincial"
    LOCAL = "LOCAL", "local"
    WARD  = "WARD", "ward"


class Office(models.Model):
    name = models.CharField(max_length=255)
    level = models.CharField(max_length=16, choices=OfficeLevels.choices)
    parent_office = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.PROTECT,
    )
    location_code = models.CharField(max_length=64, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["level"]),
            models.Index(fields=["location_code"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.level})"
