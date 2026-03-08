# Chapter 25 — Deep Dive: `users/models.py`, `users/serializers.py`, `users/views.py`

## Build Roadmap Position
- Stage: Deep Dive
- You are here: Chapter 25
- Before this: Chapter 24
- After this: Chapter 26

## Learning Objectives
- Understand user-role schema and privilege safeguards in update flows.
- `users/models.py`
- `users/serializers.py`

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 25 — Deep Dive: `users/models.py`, `users/serializers.py`, `users/views.py`

## Learning Goals
- Understand user-role schema and privilege safeguards in update flows.

## Reference Files
- `users/models.py`
- `users/serializers.py`
- `users/views.py`

## Deep Dive Walkthrough

## 1) Model (`users/models.py`)
- `UserRoles` defines project role constants.
- `User` extends `AbstractUser` with:
  - `full_name_nepali`,
  - `role`,
  - optional `office` FK.

## 2) Serializer (`users/serializers.py`)
- Adds `password` + `confirm_password` write-only fields.
- `validate` enforces match when either password field is present.
- `create` hashes password if provided.
- `update` blocks self-service changes to privileged fields:
  - `role`, `office`, `is_active`.

## 3) Viewset (`users/views.py`)
- `UserViewSet` uses filtering/search/ordering.
- Permission behavior by action:
  - `create`: `AllowAny` only if no users exist, else `IsAdminUser`.
  - `list`, `destroy`: admin only.
  - `retrieve`, `update`, `partial_update`: authenticated + self-or-admin object check.
- Non-staff queryset is restricted to self record only.

## 4) Security behavior verified by tests
- `users/tests.py` confirms non-staff user cannot elevate own role or deactivate self through PATCH.

## Chapter 25 Outcome
You now understand the complete user management safety model: bootstrap-first-user behavior, strict admin controls, and self-update restrictions.
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

