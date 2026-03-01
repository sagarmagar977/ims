import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update the initial admin user from environment variables."

    def handle(self, *args, **options):
        username = (os.getenv("BOOTSTRAP_ADMIN_USERNAME") or "").strip()
        password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD") or ""
        email = (os.getenv("BOOTSTRAP_ADMIN_EMAIL") or "").strip()
        first_name = (os.getenv("BOOTSTRAP_ADMIN_FIRST_NAME") or "").strip()
        last_name = (os.getenv("BOOTSTRAP_ADMIN_LAST_NAME") or "").strip()

        if not username:
            self.stdout.write("BOOTSTRAP_ADMIN_USERNAME not set; skipping bootstrap admin.")
            return

        if not password:
            self.stdout.write("BOOTSTRAP_ADMIN_PASSWORD not set; skipping bootstrap admin.")
            return

        User = get_user_model()
        defaults = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        }

        role_field = User._meta.get_field("role") if any(field.name == "role" for field in User._meta.fields) else None
        if role_field is not None:
            defaults["role"] = "SUPER_ADMIN"

        user, created = User.objects.get_or_create(username=username, defaults=defaults)

        changed_fields = []
        for field, value in defaults.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                changed_fields.append(field)

        if not user.check_password(password):
            user.set_password(password)
            changed_fields.append("password")

        if created:
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created bootstrap admin '{username}'."))  # noqa: B950
            return

        if changed_fields:
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Updated bootstrap admin '{username}'."))  # noqa: B950
            return

        self.stdout.write(f"Bootstrap admin '{username}' already configured.")
