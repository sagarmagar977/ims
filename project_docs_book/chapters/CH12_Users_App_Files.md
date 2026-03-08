# Chapter 12 — Users App Files

## Build Roadmap Position
- Stage: Core Domain
- You are here: Chapter 12
- Before this: Chapter 11
- After this: Chapter 13

## Learning Objectives
- Understand the custom user model used in this project.
- Learn how user APIs enforce bootstrap and privilege boundaries.
- Map how users integrate with roles and office hierarchy.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 12 — Users App Files

## Learning Goals
- Understand the custom user model used in this project.
- Learn how user APIs enforce bootstrap and privilege boundaries.
- Map how users integrate with roles and office hierarchy.

## Reference Files
- `users/models.py`
- `users/serializers.py`
- `users/views.py`
- `users/urls.py`
- `users/tests.py`
- `users/admin.py`
- `users/apps.py`
- `users/migrations/0001_initial.py`
- `users/migrations/0002_alter_user_role.py`
- `users/migrations/0003_user_office.py`

## File Breakdown

## 1) `users/models.py`
### `UserRoles`
- Role enum stored as `TextChoices`:
  - `SUPER_ADMIN`
  - `CENTRAL_ADMIN`
  - `CENTRAL_PROCUREMENT_STORE`
  - `PROVINCIAL_ADMIN`
  - `LOCAL_ADMIN`
  - `WARD_OFFICER`
  - `FINANCE`
  - `AUDIT`

### `User` model
- Extends Django `AbstractUser`.
- Adds IMS-specific fields:
  - `full_name_nepali`
  - `role` (choices from `UserRoles`)
  - `office` (FK to `hierarchy.Office`, nullable, `SET_NULL`)
- `__str__` returns full name fallback to username.

## 2) `users/serializers.py`
### `UserSerializer`
Key behaviors:
- Includes write-only `password` and `confirm_password` fields.
- Validation requires matching password pair when either is provided.
- `create()` hashes password with `set_password`.
- `update()` enforces self-service restriction:
  - Non-staff users cannot change own `role`, `office`, or `is_active`.

This serializer is the primary privilege-escalation protection for self-profile updates.

## 3) `users/views.py`
### `IsSelfOrAdmin` object permission
- Allows object access if requester is staff or owner of that user record.

### `UserViewSet`
Main behaviors:
- CRUD API with filtering/search/ordering.
- Action-specific permission policy:
  - `create`:
    - `AllowAny` only if no users exist (bootstrap path).
    - otherwise `IsAdminUser`.
  - `list`, `destroy`: `IsAdminUser`.
  - `retrieve`, `update`, `partial_update`: authenticated + self-or-admin object check.
- Queryset scoping:
  - staff sees all users.
  - non-staff sees only own user row.

This creates a controlled user-management pipeline with first-user bootstrap and strict non-admin boundaries.

## 4) `users/urls.py`
- DRF router registers `UserViewSet` at `/users`.
- Effective endpoints available under both `/api/users/` and `/api/v1/users/` via root URL includes.

## 5) `users/tests.py`
### `UserPrivilegeEscalationTests`
- Verifies a ward user cannot self-escalate privileged fields (`role`, `is_active`).
- Expected outcome: `400` and unchanged DB state.

This test directly validates serializer-side privilege protection.

## 6) `users/admin.py`
### `CustomUserAdmin`
- Extends Django `UserAdmin`.
- Adds IMS fieldset (`full_name_nepali`, `role`, `office`).
- Configures list display/filter by role and office.

## 7) `users/apps.py`
- Declares Django app config: `UsersConfig` with `name='users'`.

## 8) Migrations Summary
- `0001_initial.py`:
  - creates custom `User` table with initial role choices.
- `0002_alter_user_role.py`:
  - adds `CENTRAL_PROCUREMENT_STORE` role choice.
- `0003_user_office.py`:
  - adds `office` FK to hierarchy office table.

## Users App Responsibilities (Observed)
- identity model extension for IMS domain
- role attachment to users
- office linkage for scope-based access across system
- guarded user CRUD interface with bootstrap-safe creation path

## Security and Access Notes
- Defense is layered:
  - view-level action permissions
  - object-level self/admin checks
  - queryset restriction for non-staff
  - serializer-level protection against self privilege escalation

## Chapter 12 Outcome
You now have a full users-app map: schema, API behavior, bootstrap mechanics, privilege boundaries, admin integration, and migration evolution.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
### File: `users/models.py`
```python
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


```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `users/serializers.py`
```python
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "confirm_password",
            "first_name",
            "last_name",
            "full_name_nepali",
            "email",
            "role",
            "office",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")

        if password is not None or confirm_password is not None:
            if not password:
                raise serializers.ValidationError({"password": "Password is required when confirm_password is provided."})
            if not confirm_password:
                raise serializers.ValidationError({"confirm_password": "Please confirm the password."})
            if password != confirm_password:
                raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        validated_data.pop("confirm_password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated and not request.user.is_staff and request.user.pk == instance.pk:
            protected_fields = ("role", "office", "is_active")
            changed_protected = [field for field in protected_fields if field in validated_data]
            if changed_protected:
                raise serializers.ValidationError(
                    {
                        "detail": (
                            "You cannot update privileged account fields "
                            "(role, office, is_active) on your own profile."
                        )
                    }
                )

        password = validated_data.pop("password", None)
        validated_data.pop("confirm_password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `users/views.py`
```python
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, BasePermission, IsAdminUser, IsAuthenticated

from .models import User
from .serializers import UserSerializer


class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated and (request.user.is_staff or obj.pk == request.user.pk))


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    filterset_fields = ["role", "office", "is_active"]
    search_fields = ["username", "first_name", "last_name", "full_name_nepali", "email", "office__name"]
    ordering_fields = ["id", "username", "date_joined"]
    ordering = ["id"]

    def get_permissions(self):
        if self.action == "create":
            if not User.objects.exists():
                return [AllowAny()]
            return [IsAdminUser()]
        if self.action in ["list", "destroy"]:
            return [IsAdminUser()]
        if self.action in ["retrieve", "update", "partial_update"]:
            return [IsAuthenticated(), IsSelfOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(pk=self.request.user.pk)

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `users/urls.py`
```python
from rest_framework.routers import DefaultRouter

from .views import UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = router.urls

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `users/tests.py`
```python
from rest_framework import status
from rest_framework.test import APITestCase

from hierarchy.models import Office, OfficeLevels
from users.models import User, UserRoles


class UserPrivilegeEscalationTests(APITestCase):
    def setUp(self):
        self.central = Office.objects.create(name="Central", level=OfficeLevels.CENTRAL, location_code="CENTRAL-1")
        self.user = User.objects.create_user(
            username="ward_user",
            password="pass12345",
            role=UserRoles.WARD_OFFICER,
            office=self.central,
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_self_update_cannot_change_privileged_fields(self):
        payload = {
            "role": UserRoles.SUPER_ADMIN,
            "is_active": False,
        }
        response = self.client.patch(f"/api/users/{self.user.id}/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, UserRoles.WARD_OFFICER)
        self.assertTrue(self.user.is_active)

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `users/admin.py`
```python
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

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `users/apps.py`
```python
from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'users'

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `users/migrations/0001_initial.py`
```python
# Generated by Django 6.0.2 on 2026-02-24 08:00

import django.contrib.auth.models
import django.contrib.auth.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('full_name_nepali', models.CharField(blank=True, max_length=255, null=True)),
                ('role', models.CharField(blank=True, choices=[('SUPER_ADMIN', 'Super Admin'), ('CENTRAL_ADMIN', 'Central Admin'), ('PROVINCIAL_ADMIN', 'Provincial Admin'), ('LOCAL_ADMIN', 'Local Admin'), ('WARD_OFFICER', 'Ward Officer'), ('FINANCE', 'Finance'), ('AUDIT', 'Audit')], max_length=225, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `users/migrations/0002_alter_user_role.py`
```python
# Generated by Django 6.0.2 on 2026-02-25 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(blank=True, choices=[('SUPER_ADMIN', 'Super Admin'), ('CENTRAL_ADMIN', 'Central Admin'), ('CENTRAL_PROCUREMENT_STORE', 'Central Procurement/Store'), ('PROVINCIAL_ADMIN', 'Provincial Admin'), ('LOCAL_ADMIN', 'Local Admin'), ('WARD_OFFICER', 'Ward Officer'), ('FINANCE', 'Finance'), ('AUDIT', 'Audit')], max_length=225, null=True),
        ),
    ]

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `users/migrations/0003_user_office.py`
```python
# Generated by Django 6.0.2 on 2026-02-25 18:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hierarchy', '0002_alter_office_level'),
        ('users', '0002_alter_user_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='office',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='hierarchy.office'),
        ),
    ]

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

## Rebuild Step (Hands-on Roadmap)
- Implement or review the files listed in this chapter only.
- Validate behavior discussed in the original chapter explanation.
- Confirm readiness for the next chapter transition.

## Chapter Summary
This chapter ties repository explanation to exact code references and prepares the next build step.

## Files Used
- `users/models.py`
- `users/serializers.py`
- `users/views.py`
- `users/urls.py`
- `users/tests.py`
- `users/admin.py`
- `users/apps.py`
- `users/migrations/0001_initial.py`
- `users/migrations/0002_alter_user_role.py`
- `users/migrations/0003_user_office.py`

