# Chapter 9 — State Management (if exists)

## Build Roadmap Position
- Stage: Execution Flow
- You are here: Chapter 9
- Before this: Chapter 8
- After this: Chapter 10

## Learning Objectives
- Identify what "state" is managed in this backend.
- Distinguish persistent state, auth state, and request-scoped derived state.
- Confirm which common state-management patterns are not present.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 9 — State Management (if exists)

## Learning Goals
- Identify what "state" is managed in this backend.
- Distinguish persistent state, auth state, and request-scoped derived state.
- Confirm which common state-management patterns are not present.

## Reference Files
- `django_project/settings.py`
- `users/models.py`
- `inventory/models.py`
- `actions/models.py`
- `audit/models.py`
- `common/access.py`
- `common/permissions.py`

## State Management Exists: Yes (Backend-Persistent + Request-Derived)
This project manages state primarily through:
1. Database-backed domain state (Django models)
2. JWT-based authentication state
3. Request-time derived access scope state
4. Audit timeline state

## 1) Persistent Domain State (Primary)
State is persisted in relational tables via Django models.

Key persistent state groups:
- User and role state:
  - `users.User` with `role`, `office`, and standard auth fields.
- Inventory lifecycle state:
  - `InventoryItem.status` (`ACTIVE`, `INACTIVE`, `DISPOSED`, etc.)
  - `InventoryItem.item_type` (`FIXED_ASSET` / `CONSUMABLE`)
- Consumable stock state:
  - `ConsumableStock.quantity`, `min_threshold`, `reorder_alert_enabled`.
- Assignment state:
  - `ItemAssignment.status` (`ASSIGNED` / `RETURNED`) plus return metadata.
- Audit/history state:
  - `InventoryAuditLog` with before/after JSON snapshots and timestamps.

This is the core state model of the system.

## 2) Authentication State
Auth state is handled by JWT:
- Global DRF auth class: `rest_framework_simplejwt.authentication.JWTAuthentication`.
- Requests are authenticated by bearer token, not by server-side custom session store in app code.

Related note:
- Django `SessionMiddleware` is present in middleware stack (framework default), but this codebase’s API auth path is JWT-based.

## 3) Authorization/Access Scope State (Derived Per Request)
`common/access.py` computes effective data scope from user role + office hierarchy:
- Global roles -> unrestricted queryset scope.
- Scoped roles -> office-descendant filtered scope.
- Ward officer -> own office scope.

This is a derived runtime state, recomputed from persisted user/office data.

## 4) Policy State (Role Matrix)
`common/permissions.py` defines role-policy state in code constants:
- read-only role set,
- write role set,
- per-resource write matrix.

This policy state is static code-level configuration, not database-configurable in current files.

## 5) State Transitions Implemented
State transitions are explicit in domain flows:
- Stock transition:
  - transaction type + quantity changes `ConsumableStock.quantity`.
- Assignment transition:
  - `ASSIGNED -> RETURNED` with `returned_at` requirements.
- Inventory activity transition:
  - create/update/assign/return events recorded to audit log.

These transitions are enforced through serializers, model constraints, and view hooks.

## 6) Consistency Controls for State
Observed controls include:
- Model constraints (check/unique constraints in assignments).
- Serializer validation rules (item type vs category, stock quantity checks).
- Atomic DB transaction in consumable stock transaction serializer create.
- Indexed state fields for query performance (`status`, relation/time indexes).

## What Is Not Present
From scanned repository files:
- No frontend client-state store (Redux/Zustand/etc.) in this backend repo.
- No explicit distributed cache layer wiring in settings (for example configured `CACHES` backend).
- No event-sourcing framework; audit log is present but primary state remains relational model state.
- No workflow engine/state machine library usage detected.

## State Management Summary
State management is database-centric and request-driven:
- persistent domain state in models,
- access/auth state resolved per request,
- transitions validated in serializers/models,
- side-effect state captured in audit logs.

## Chapter 9 Outcome
You now understand exactly how state is stored, derived, protected, and transitioned in this backend, and which advanced state-management mechanisms are not implemented in current project code.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
### File: `django_project/settings.py`
```python
"""
Django settings for django_project project.
"""

import importlib.util
import os
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name, default=None):
    value = os.getenv(name)
    if value is None:
        return list(default or [])
    return [item.strip() for item in value.split(",") if item.strip()]


def _resolve_default_sqlite_path():
    candidates = [
        Path(os.getenv("LOCALAPPDATA", "")) / "ims" if os.getenv("LOCALAPPDATA") else None,
        Path(tempfile.gettempdir()) / "ims",
        BASE_DIR,
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate / "db.sqlite3"
        except OSError:
            continue
    return BASE_DIR / "db.sqlite3"


def _database_from_url(database_url):
    parsed = urlparse(database_url)
    engine_map = {
        "postgres": "django.db.backends.postgresql",
        "postgresql": "django.db.backends.postgresql",
        "pgsql": "django.db.backends.postgresql",
        "sqlite": "django.db.backends.sqlite3",
    }
    engine = engine_map.get(parsed.scheme)
    if not engine:
        raise ValueError(f"Unsupported DATABASE_URL scheme: {parsed.scheme}")

    if engine == "django.db.backends.sqlite3":
        return {"ENGINE": engine, "NAME": unquote(parsed.path.lstrip("/")) or str(DEFAULT_SQLITE_PATH)}

    query = parse_qs(parsed.query)
    options = {}
    sslmode = query.get("sslmode", [None])[0]
    if sslmode:
        options["sslmode"] = sslmode

    return {
        "ENGINE": engine,
        "NAME": unquote(parsed.path.lstrip("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or ""),
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "600")),
        **({"OPTIONS": options} if options else {}),
    }


DEFAULT_SQLITE_PATH = _resolve_default_sqlite_path()

IS_RENDER = _env_bool("RENDER", False) or bool(os.getenv("RENDER_EXTERNAL_HOSTNAME"))
HAS_CORSHEADERS = importlib.util.find_spec("corsheaders") is not None

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-local-dev-only-change-me")
DEBUG = _env_bool("DEBUG", default=not IS_RENDER)
ENABLE_SWAGGER = _env_bool("ENABLE_SWAGGER", default=DEBUG)

ALLOWED_HOSTS = _env_list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "testserver"])
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = _env_list("CSRF_TRUSTED_ORIGINS", default=[])
if RENDER_EXTERNAL_HOSTNAME:
    origin = f"https://{RENDER_EXTERNAL_HOSTNAME}"
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

INSTALLED_APPS = [
    "users",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "drf_spectacular",
    "hierarchy",
    "catalog",
    "inventory",
    "actions",
    "audit",
    "reports",
    "common",
]
if HAS_CORSHEADERS:
    INSTALLED_APPS.insert(7, "corsheaders")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "common.middleware.LegacyApiDeprecationMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if HAS_CORSHEADERS:
    MIDDLEWARE.insert(1, "corsheaders.middleware.CorsMiddleware")

if importlib.util.find_spec("whitenoise"):
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "django_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "django_project.wsgi.application"

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {"default": _database_from_url(DATABASE_URL)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.getenv("SQLITE_DB_PATH", str(DEFAULT_SQLITE_PATH)),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
if importlib.util.find_spec("whitenoise"):
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    WHITENOISE_MANIFEST_STRICT = False

AUTH_USER_MODEL = "users.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("DRF_THROTTLE_ANON", "60/min"),
        "user": os.getenv("DRF_THROTTLE_USER", "300/min"),
    },
}

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "ims@localhost")
LOW_STOCK_ALERT_EMAILS = [
    email.strip()
    for email in os.getenv("LOW_STOCK_ALERT_EMAILS", "").split(",")
    if email.strip()
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

if not DEBUG:
    if SECRET_KEY == "django-insecure-local-dev-only-change-me" or len(SECRET_KEY) < 50:
        raise ImproperlyConfigured("Set a strong SECRET_KEY environment variable for production.")
    if not ALLOWED_HOSTS or ALLOWED_HOSTS == ["localhost", "127.0.0.1", "testserver"]:
        raise ImproperlyConfigured("Set ALLOWED_HOSTS for production.")
    if not DATABASE_URL and not _env_bool("ALLOW_SQLITE_IN_PROD", False):
        raise ImproperlyConfigured(
            "Set DATABASE_URL for production (or ALLOW_SQLITE_IN_PROD=true for temporary use)."
        )

    SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = _env_bool("SECURE_HSTS_PRELOAD", True)

# CORS configuration for frontend on separate host/machine.
CORS_ALLOW_ALL_ORIGINS = _env_bool("CORS_ALLOW_ALL_ORIGINS", False)
CORS_ALLOWED_ORIGINS = _env_list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = _env_bool("CORS_ALLOW_CREDENTIALS", True)
FRONTEND_URL = (os.getenv("FRONTEND_URL") or "").strip().rstrip("/")
if FRONTEND_URL:
    if FRONTEND_URL not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(FRONTEND_URL)
    if FRONTEND_URL not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(FRONTEND_URL)

SPECTACULAR_SETTINGS = {
    "TITLE": "IMS API",
    "DESCRIPTION": "Inventory Management System API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
    },
}

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

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

### File: `inventory/models.py`
```python
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

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `actions/models.py`
```python
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

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `audit/models.py`
```python
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

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `common/access.py`
```python
from users.models import UserRoles
from hierarchy.models import Office


GLOBAL_ROLES = {
    UserRoles.SUPER_ADMIN,
    UserRoles.CENTRAL_ADMIN,
    UserRoles.CENTRAL_PROCUREMENT_STORE,
    UserRoles.FINANCE,
    UserRoles.AUDIT,
}

SCOPED_ROLES = {
    UserRoles.PROVINCIAL_ADMIN,
    UserRoles.LOCAL_ADMIN,
    UserRoles.WARD_OFFICER,
}


def get_descendant_office_ids(root_office_id):
    if not root_office_id:
        return []
    office_ids = {root_office_id}
    frontier = {root_office_id}
    while frontier:
        child_ids = set(
            Office.objects.filter(parent_office_id__in=frontier).values_list("id", flat=True)
        ) - office_ids
        if not child_ids:
            break
        office_ids.update(child_ids)
        frontier = child_ids
    return list(office_ids)


def get_accessible_office_ids(user):
    if user.is_staff or user.is_superuser:
        return None
    if user.role in GLOBAL_ROLES:
        return None
    if user.role in SCOPED_ROLES:
        if user.role == UserRoles.WARD_OFFICER:
            return [user.office_id] if user.office_id else []
        return get_descendant_office_ids(user.office_id)
    return []


def scope_queryset_by_user(queryset, user, office_lookup):
    office_ids = get_accessible_office_ids(user)
    if office_ids is None:
        return queryset
    return queryset.filter(**{f"{office_lookup}__in": office_ids})

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `common/permissions.py`
```python
from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.models import UserRoles


READ_ONLY_ROLES = {
    UserRoles.FINANCE,
    UserRoles.AUDIT,
}

WRITE_ROLES = {
    UserRoles.SUPER_ADMIN,
    UserRoles.CENTRAL_ADMIN,
    UserRoles.CENTRAL_PROCUREMENT_STORE,
    UserRoles.PROVINCIAL_ADMIN,
    UserRoles.LOCAL_ADMIN,
    UserRoles.WARD_OFFICER,
}

WRITE_ROLE_MATRIX = {
    "office": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
    },
    "category": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
    },
    "custom-field-definition": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
    },
    "inventory-item": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
        UserRoles.CENTRAL_PROCUREMENT_STORE,
        UserRoles.PROVINCIAL_ADMIN,
        UserRoles.LOCAL_ADMIN,
    },
    "fixed-asset": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
        UserRoles.CENTRAL_PROCUREMENT_STORE,
        UserRoles.PROVINCIAL_ADMIN,
        UserRoles.LOCAL_ADMIN,
    },
    "consumable-stock": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
        UserRoles.CENTRAL_PROCUREMENT_STORE,
        UserRoles.PROVINCIAL_ADMIN,
        UserRoles.LOCAL_ADMIN,
    },
    "consumable-stock-transaction": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
        UserRoles.CENTRAL_PROCUREMENT_STORE,
        UserRoles.PROVINCIAL_ADMIN,
        UserRoles.LOCAL_ADMIN,
        UserRoles.WARD_OFFICER,
    },
    "item-assignment": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
        UserRoles.CENTRAL_PROCUREMENT_STORE,
        UserRoles.PROVINCIAL_ADMIN,
        UserRoles.LOCAL_ADMIN,
    },
    "inventory-audit-log": set(),
}


class IMSAccessPermission(BasePermission):
    """
    Role baseline from PRD:
    - Finance/Audit: read-only
    - Operational/admin roles: read-write
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_staff or user.is_superuser:
            return True

        if request.method in SAFE_METHODS:
            return bool(user.role)

        if user.role in READ_ONLY_ROLES:
            return False

        view_basename = getattr(view, "basename", None)
        if view_basename in WRITE_ROLE_MATRIX:
            return user.role in WRITE_ROLE_MATRIX[view_basename]

        return user.role in WRITE_ROLES

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
- `django_project/settings.py`
- `users/models.py`
- `inventory/models.py`
- `actions/models.py`
- `audit/models.py`
- `common/access.py`
- `common/permissions.py`

