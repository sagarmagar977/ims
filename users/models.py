from django.db import models

from django.contrib.auth.models import AbstractUser

# Create your models here.


class UserRoles(models.TextChoices): 
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    CENTRAL_ADMIN = "CENTRAL_ADMIN", "Central Admin"
    CENTRAL_PROCUREMENT_STORE = "CENTRAL_PROCUREMENT_STORE", "Central Procurement/Store"
    PROVINCIAL_ADMIN = "PROVINCIAL_ADMIN", "Provincial Admin"
    LOCAL_ADMIN = "LOCAL_ADMIN", "Local Admin"
    WARD_OFFICER = "WARD_OFFICER", "Ward Officer"
    FINANCE = "FINANCE", "Finance"
    AUDIT = "AUDIT", "Audit"






class User(AbstractUser):
    full_name_nepali = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=225, choices = UserRoles.choices,null=True, blank=True)
    office = models.ForeignKey("hierarchy.Office", null=True, blank=True, on_delete=models.SET_NULL, related_name="users")

    def __str__(self) -> str:
        return self.get_full_name() or self.username

