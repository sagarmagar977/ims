from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("IMS", {"fields": ("full_name_nepali", "role", "office")}),
    )
    list_display = ("username", "email", "role", "office", "is_staff", "is_active")
    list_filter = ("role", "office", "is_staff", "is_active")
