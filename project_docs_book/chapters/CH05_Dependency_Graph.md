# Chapter 5 — Dependency Graph

## Build Roadmap Position
- Stage: Foundation
- You are here: Chapter 5
- Before this: Chapter 4
- After this: Chapter 6

## Learning Objectives
- Understand how apps depend on each other.
- Identify central shared modules and high-coupling points.
- Recognize dependency direction between domain modules.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 5 — Dependency Graph

## Learning Goals
- Understand how apps depend on each other.
- Identify central shared modules and high-coupling points.
- Recognize dependency direction between domain modules.

## Reference Files
- `django_project/settings.py`
- `django_project/urls.py`
- `users/models.py`, `users/views.py`
- `hierarchy/models.py`, `hierarchy/views.py`
- `catalog/models.py`, `catalog/views.py`
- `inventory/models.py`, `inventory/serializers.py`, `inventory/views.py`
- `actions/models.py`, `actions/views.py`
- `audit/models.py`, `audit/views.py`, `audit/utils.py`
- `reports/views.py`
- `common/access.py`, `common/permissions.py`, `common/middleware.py`
- `common/management/commands/seed_prd_data.py`

## Project Composition Dependency
`django_project/urls.py` includes route modules from:
- `users`
- `hierarchy`
- `catalog`
- `inventory`
- `actions`
- `audit`
- `reports`

`django_project/settings.py` installs apps in this project:
- `users`, `hierarchy`, `catalog`, `inventory`, `actions`, `audit`, `reports`, `common`

## App-to-App Dependency Map (Observed Imports)
- `users` -> `hierarchy`
  - `User.office` is FK to `hierarchy.Office`.

- `hierarchy` -> `common`
  - Views use `IMSAccessPermission` and `scope_queryset_by_user`.

- `catalog` -> `common`
  - Views use `IMSAccessPermission`.

- `inventory` -> `catalog`, `hierarchy`, `audit`, `actions`, `common`
  - Models depend on `Category` and `Office`.
  - Views write audit logs via `audit`.
  - Serializers read assignment status via `actions`.
  - Views use `common` permission/scope helpers.

- `actions` -> `inventory`, `hierarchy`, `audit`, `common`
  - Models depend on `InventoryItem` and `Office`.
  - Views write audit logs via `audit`.
  - Views use `common` permission/scope helpers.

- `audit` -> `inventory`, `common`
  - Audit model FK points to `InventoryItem`.
  - Views use `common` permission/scope helpers.

- `reports` -> `inventory`, `actions`, `audit`, `hierarchy`, `common`
  - Report views aggregate across multiple domain models.

- `common` -> `users`, `hierarchy`, and (for management command) most apps
  - `permissions.py` depends on `UserRoles`.
  - `access.py` depends on `UserRoles` and `Office`.
  - `seed_prd_data.py` imports models from `users`, `hierarchy`, `catalog`, `inventory`, `actions`, `audit`.

## Dependency Graph (App Level)
```text
users ------> hierarchy
   ^             ^
   |             |
common ----------+
  |\
  | +--> inventory <------> actions
  |        |   ^             |
  |        v   |             v
  +------> audit <-----------+
           ^
           |
        reports ----> (inventory, actions, audit, hierarchy, common)

catalog ----> common
inventory --> catalog
inventory --> hierarchy
```

## High-Coupling Nodes
- `inventory` is the strongest domain hub (used by `actions`, `audit`, `reports`; also depends on several apps).
- `common` is the shared policy/scope hub (imported by multiple apps).
- `reports` is read-side aggregation over many domains.

## Bidirectional Coupling Observed
- `inventory` <-> `actions`
  - `actions.models` imports `inventory.models.InventoryItem`.
  - `inventory.serializers` imports `actions.models.AssignmentStatus`.

This is a real code-level two-way dependency in current files.

## What Is Missing
- No separate dependency management layer (for example explicit domain service interfaces) is present.
- No generated/static dependency diagram file exists in this repository.

## Chapter 5 Outcome
You now have a concrete dependency graph: `inventory` and `common` are central, `reports` is aggregation-focused, and cross-app imports define the real coupling structure of this backend.
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

### File: `django_project/urls.py`
```python
from django.contrib import admin
from django.conf import settings
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", lambda request: JsonResponse({"status": "ok"}), name="health"),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="v1-token-obtain-pair"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="v1-token-refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="v1-schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="v1-schema"), name="v1-swagger-ui"),
    path("api/", include("users.urls")),
    path("api/", include("hierarchy.urls")),
    path("api/", include("catalog.urls")),
    path("api/", include("inventory.urls")),
    path("api/", include("actions.urls")),
    path("api/", include("audit.urls")),
    path("api/", include("reports.urls")),
    path("api/v1/", include("users.urls")),
    path("api/v1/", include("hierarchy.urls")),
    path("api/v1/", include("catalog.urls")),
    path("api/v1/", include("inventory.urls")),
    path("api/v1/", include("actions.urls")),
    path("api/v1/", include("audit.urls")),
    path("api/v1/", include("reports.urls")),
]

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

### File: `hierarchy/models.py`
```python
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

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `catalog/models.py`
```python

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

### File: `reports/views.py`
```python
from django.db.models import Count, F, Q
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from actions.models import AssignmentStatus, ItemAssignment
from audit.models import InventoryAuditLog
from common.access import scope_queryset_by_user
from hierarchy.models import Office
from inventory.models import ConsumableStock, FixedAsset, InventoryItem, InventoryStatus


class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        item_qs = scope_queryset_by_user(InventoryItem.objects.all(), request.user, "office_id")
        assignment_qs = scope_queryset_by_user(ItemAssignment.objects.all(), request.user, "item__office_id")
        stock_qs = scope_queryset_by_user(ConsumableStock.objects.all(), request.user, "item__office_id")
        fixed_qs = scope_queryset_by_user(FixedAsset.objects.all(), request.user, "item__office_id")
        office_ids = item_qs.values_list("office_id", flat=True).distinct()
        assigned_count = assignment_qs.filter(status=AssignmentStatus.ASSIGNED).values("item_id").distinct().count()
        unassigned_count = max(item_qs.count() - assigned_count, 0)
        data = {
            "total_inventory_items": item_qs.count(),
            "active_inventory_items": item_qs.filter(status=InventoryStatus.ACTIVE).count(),
            "disposed_inventory_items": item_qs.filter(status=InventoryStatus.DISPOSED).count(),
            "fixed_assets": fixed_qs.count(),
            "consumable_stocks": stock_qs.count(),
            "active_assignments": assignment_qs.filter(status=AssignmentStatus.ASSIGNED).count(),
            "returned_assignments": assignment_qs.filter(status=AssignmentStatus.RETURNED).count(),
            "low_stock_items": stock_qs.filter(
                reorder_alert_enabled=True,
                quantity__lte=F("min_threshold"),
            ).count(),
            "assigned_assets": assigned_count,
            "unassigned_assets": unassigned_count,
            "active_offices": Office.objects.filter(id__in=office_ids).count(),
        }
        return Response(data)


class LowStockReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stocks_qs = scope_queryset_by_user(ConsumableStock.objects.all(), request.user, "item__office_id")
        stocks = (
            stocks_qs.select_related("item", "item__office", "item__category")
            .filter(reorder_alert_enabled=True, quantity__lte=F("min_threshold"))
            .order_by("quantity", "id")
        )

        data = [
            {
                "stock_id": stock.id,
                "item_id": stock.item_id,
                "title": stock.item.title,
                "office": stock.item.office.name,
                "category": stock.item.category.name,
                "quantity": stock.quantity,
                "min_threshold": stock.min_threshold,
                "unit": stock.unit,
            }
            for stock in stocks
        ]
        return Response(data)


class AssignmentSummaryByOfficeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        scoped_qs = scope_queryset_by_user(ItemAssignment.objects.all(), request.user, "item__office_id")
        data = list(
            scoped_qs.values("item__office__id", "item__office__name")
            .annotate(
                total=Count("id"),
                active=Count("id", filter=Q(status=AssignmentStatus.ASSIGNED)),
                returned=Count("id", filter=Q(status=AssignmentStatus.RETURNED)),
            )
            .order_by("item__office__name")
        )
        return Response(data)


class RecentInventoryActivitiesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        logs_qs = scope_queryset_by_user(InventoryAuditLog.objects.all(), request.user, "item__office_id")
        logs = (
            logs_qs.select_related("item", "performed_by")
            .all()
            .order_by("-created_at")[:50]
        )
        data = [
            {
                "id": log.id,
                "item_name": log.item.title,
                "unique_number": log.item.item_number,
                "performed_by": (log.performed_by.get_full_name() or log.performed_by.username) if log.performed_by else None,
                "date": log.created_at.date(),
                "amount": str(log.item.amount),
                "status": log.action_type,
                "action": log.remarks,
            }
            for log in logs
        ]
        return Response(data)


class InventoryReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self, request):
        queryset = scope_queryset_by_user(InventoryItem.objects.all(), request.user, "office_id").select_related("category", "office").order_by("-created_at")
        category = request.query_params.get("category")
        status = request.query_params.get("status")
        office = request.query_params.get("office")
        fiscal_year = request.query_params.get("fiscal_year")

        if category:
            queryset = queryset.filter(category_id=category)
        if status:
            queryset = queryset.filter(status=status)
        if office:
            queryset = queryset.filter(office_id=office)

        # Fiscal year format: YYYY-YYYY, window from Jul 16 first year to Jul 15 second year.
        if fiscal_year and "-" in fiscal_year:
            start_year, end_year = fiscal_year.split("-", 1)
            if start_year.isdigit() and end_year.isdigit():
                queryset = queryset.filter(
                    purchased_date__gte=f"{start_year}-07-16",
                    purchased_date__lte=f"{end_year}-07-15",
                )

        return queryset

    def get(self, request):
        queryset = self.get_queryset(request)
        data = self.serialize_items(queryset)
        return Response(data)

    @staticmethod
    def serialize_items(queryset):
        return [
            {
                "id": item.id,
                "item_name": item.title,
                "item_number": item.item_number,
                "item_type": item.item_type,
                "category": item.category.name,
                "office": item.office.name,
                "status": item.status,
                "amount": str(item.amount),
                "purchased_date": item.purchased_date,
            }
            for item in queryset
        ]


class InventoryReportExportCSVView(InventoryReportView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = self.get_queryset(request)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="inventory_report.csv"'
        response.write("item_name,item_number,item_type,category,office,status,amount,purchased_date\n")
        for item in queryset:
            response.write(
                f'"{item.title}","{item.item_number or ""}","{item.item_type}","{item.category.name}","{item.office.name}","{item.status}","{item.amount}","{item.purchased_date or ""}"\n'
            )
        return response


class InventoryReportExportExcelView(InventoryReportView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = self.get_queryset(request)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Inventory Report"

        headers = ["Item Name", "Item Number", "Item Type", "Category", "Office", "Status", "Amount", "Purchased Date"]
        sheet.append(headers)

        for item in queryset:
            sheet.append(
                [
                    item.title,
                    item.item_number or "",
                    item.item_type,
                    item.category.name,
                    item.office.name,
                    item.status,
                    float(item.amount),
                    item.purchased_date.isoformat() if item.purchased_date else "",
                ]
            )

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="inventory_report.xlsx"'
        workbook.save(response)
        return response


class InventoryReportExportPDFView(InventoryReportView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = self.get_queryset(request)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="inventory_report.pdf"'

        pdf = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        y = height - 40

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, "DoNIDCR - Inventory Report")
        y -= 20

        pdf.setFont("Helvetica", 9)
        pdf.drawString(40, y, "Item Name")
        pdf.drawString(210, y, "Item Number")
        pdf.drawString(300, y, "Category")
        pdf.drawString(390, y, "Office")
        pdf.drawString(480, y, "Status")
        y -= 14

        for item in queryset:
            if y < 50:
                pdf.showPage()
                y = height - 40
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(40, y, "DoNIDCR - Inventory Report (cont.)")
                y -= 20
                pdf.setFont("Helvetica", 9)

            pdf.drawString(40, y, (item.title or "")[:28])
            pdf.drawString(210, y, (item.item_number or "")[:14])
            pdf.drawString(300, y, (item.category.name or "")[:14])
            pdf.drawString(390, y, (item.office.name or "")[:14])
            pdf.drawString(480, y, (item.status or "")[:10])
            y -= 14

        pdf.save()
        return response

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

### File: `common/management/commands/seed_prd_data.py`
```python
from datetime import date, datetime, timezone
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from actions.models import AssignmentStatus, ItemAssignment, ItemCondition
from audit.models import InventoryActionType, InventoryAuditLog
from catalog.models import Category, CustomFieldDefinition, CustomFieldType
from hierarchy.models import Office, OfficeLevels
from inventory.models import (
    ConsumableStock,
    ConsumableStockTransaction,
    FixedAsset,
    InventoryItem,
    InventoryItemType,
    InventoryStatus,
    StockTransactionType,
)
from users.models import User, UserRoles


OFFICES = [
    ("DoNIDCR Central Office", OfficeLevels.CENTRAL, None, "NPL-CENTRAL-001"),
    ("Province 1 Office", OfficeLevels.PROVINCIAL, "NPL-CENTRAL-001", "NPL-P1-001"),
    ("Province 2 Office", OfficeLevels.PROVINCIAL, "NPL-CENTRAL-001", "NPL-P2-001"),
    ("Kathmandu Metropolitan Office", OfficeLevels.LOCAL, "NPL-P1-001", "NPL-L1-001"),
    ("Lalitpur Metropolitan Office", OfficeLevels.LOCAL, "NPL-P1-001", "NPL-L1-002"),
    ("Ward 1 Registration Point", OfficeLevels.WARD, "NPL-L1-001", "NPL-W1-001"),
    ("Ward 2 Registration Point", OfficeLevels.WARD, "NPL-L1-001", "NPL-W1-002"),
]

USERS = [
    ("superadmin", "SUPER_ADMIN", True, "NPL-CENTRAL-001"),
    ("central_admin", "CENTRAL_ADMIN", True, "NPL-CENTRAL-001"),
    ("store_keeper", "CENTRAL_PROCUREMENT_STORE", False, "NPL-CENTRAL-001"),
    ("prov_admin_p1", "PROVINCIAL_ADMIN", False, "NPL-P1-001"),
    ("local_admin_ktm", "LOCAL_ADMIN", False, "NPL-L1-001"),
    ("ward_officer_1", "WARD_OFFICER", False, "NPL-W1-001"),
    ("finance_user", "FINANCE", False, "NPL-CENTRAL-001"),
    ("audit_user", "AUDIT", False, "NPL-CENTRAL-001"),
]

CUSTOM_FIELDS = [
    ("Laptop", "RAM", CustomFieldType.SELECT, True, False, ["8GB", "16GB", "32GB"]),
    ("Laptop", "Processor", CustomFieldType.TEXT, True, False, []),
    ("Laptop", "Storage", CustomFieldType.SELECT, True, False, ["256GB SSD", "512GB SSD", "1TB SSD"]),
    ("Printer", "Model", CustomFieldType.TEXT, True, False, []),
    ("Printer", "Ink Type", CustomFieldType.SELECT, True, False, ["Inkjet", "Laser Toner"]),
    ("Biometric Device", "Vendor", CustomFieldType.TEXT, True, False, []),
    ("Registration Forms", "Form Type", CustomFieldType.SELECT, True, False, ["Birth", "Death", "Marriage"]),
    ("Stationery", "Unit", CustomFieldType.TEXT, True, False, []),
    ("Toner/Ink", "Color", CustomFieldType.SELECT, False, False, ["Black", "Cyan", "Magenta", "Yellow"]),
]

ITEMS = [
    {
        "item_number": "FA-0001",
        "title": "Dell Latitude 5440",
        "category": "Laptop",
        "office_code": "NPL-W1-001",
        "item_type": InventoryItemType.FIXED_ASSET,
        "status": InventoryStatus.ACTIVE,
        "amount": Decimal("120000.00"),
        "price": Decimal("120000.00"),
        "currency": "NPR",
        "department": "Registration",
        "manufacturer": "Dell",
        "purchased_date": date(2025, 7, 20),
        "dynamic_data": {"RAM": "16GB", "Processor": "Intel i7", "Storage": "512GB SSD"},
        "fixed_asset": {
            "asset_tag": "LAP-W1-0001",
            "serial_number": "SN-LAP-0001",
            "purchase_date": date(2025, 7, 20),
            "warranty_expiry_date": date(2028, 7, 20),
        },
    },
    {
        "item_number": "FA-0002",
        "title": "HP LaserJet Pro",
        "category": "Printer",
        "office_code": "NPL-L1-001",
        "item_type": InventoryItemType.FIXED_ASSET,
        "status": InventoryStatus.ACTIVE,
        "amount": Decimal("45000.00"),
        "price": Decimal("45000.00"),
        "currency": "NPR",
        "department": "Office Operations",
        "manufacturer": "HP",
        "purchased_date": date(2025, 8, 10),
        "dynamic_data": {"Model": "M404dn", "Ink Type": "Laser Toner"},
        "fixed_asset": {
            "asset_tag": "PRN-L1-0001",
            "serial_number": "SN-PRN-0001",
            "purchase_date": date(2025, 8, 10),
            "warranty_expiry_date": date(2027, 8, 10),
        },
    },
    {
        "item_number": "CON-0001",
        "title": "Citizen Registration Form",
        "category": "Registration Forms",
        "office_code": "NPL-W1-001",
        "item_type": InventoryItemType.CONSUMABLE,
        "status": InventoryStatus.ACTIVE,
        "amount": Decimal("10000.00"),
        "price": Decimal("10.00"),
        "currency": "NPR",
        "department": "Registration",
        "manufacturer": "Govt Printing Press",
        "purchased_date": date(2025, 7, 25),
        "dynamic_data": {"Form Type": "Birth"},
        "consumable_stock": {
            "initial_quantity": Decimal("1000"),
            "quantity": Decimal("920"),
            "min_threshold": Decimal("200"),
            "unit": "pcs",
        },
    },
    {
        "item_number": "CON-0002",
        "title": "A4 Office Paper",
        "category": "Stationery",
        "office_code": "NPL-L1-001",
        "item_type": InventoryItemType.CONSUMABLE,
        "status": InventoryStatus.ACTIVE,
        "amount": Decimal("15000.00"),
        "price": Decimal("500.00"),
        "currency": "NPR",
        "department": "Admin",
        "manufacturer": "Nepal Paper Co",
        "purchased_date": date(2025, 9, 1),
        "dynamic_data": {"Unit": "ream"},
        "consumable_stock": {
            "initial_quantity": Decimal("100"),
            "quantity": Decimal("60"),
            "min_threshold": Decimal("20"),
            "unit": "ream",
        },
    },
]


class Command(BaseCommand):
    help = "Seed PRD-aligned sample data across core IMS tables (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing data.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        self.stdout.write("Seeding PRD-aligned data...")

        with transaction.atomic():
            call_command("seed_initial_categories", dry_run=dry_run, stdout=self.stdout)

            offices = self._seed_offices(dry_run=dry_run)
            users = self._seed_users(offices=offices, dry_run=dry_run)
            self._seed_custom_fields(dry_run=dry_run)
            items = self._seed_inventory(offices=offices, dry_run=dry_run)
            self._seed_assignments(items=items, users=users, offices=offices, dry_run=dry_run)
            self._seed_stock_transactions(items=items, users=users, dry_run=dry_run)
            self._seed_audit_logs(items=items, users=users, dry_run=dry_run)

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("Dry run enabled. Rolled back all changes."))

        self.stdout.write(self.style.SUCCESS("PRD seed completed."))

    def _seed_offices(self, dry_run=False):
        office_by_code = {o.location_code: o for o in Office.objects.all()}
        created = 0
        updated = 0

        for name, level, parent_code, code in OFFICES:
            parent = office_by_code.get(parent_code) if parent_code else None
            obj = Office.objects.filter(location_code=code).first()
            if obj is None:
                created += 1
                if not dry_run:
                    obj = Office.objects.create(name=name, level=level, parent_office=parent, location_code=code)
                office_by_code[code] = obj
                self.stdout.write(self.style.SUCCESS(f"{'Would create' if dry_run else 'Created'} office: {code}"))
                continue

            changed = False
            if obj.name != name:
                obj.name = name
                changed = True
            if obj.level != level:
                obj.level = level
                changed = True
            if obj.parent_office_id != (parent.id if parent else None):
                obj.parent_office = parent
                changed = True
            if changed:
                updated += 1
                if not dry_run:
                    obj.save(update_fields=["name", "level", "parent_office"])
                self.stdout.write(self.style.WARNING(f"{'Would update' if dry_run else 'Updated'} office: {code}"))
            office_by_code[code] = obj

        self.stdout.write(f"Offices: created={created}, updated={updated}, total={len(office_by_code)}")
        return office_by_code

    def _seed_users(self, offices, dry_run=False):
        users = {}
        created = 0
        updated = 0

        for username, role, is_staff, office_code in USERS:
            office = offices.get(office_code)
            defaults = {
                "email": f"{username}@ims.local",
                "first_name": username.replace("_", " ").title(),
                "role": role,
                "is_staff": is_staff,
                "is_active": True,
                "office": office,
            }
            obj = User.objects.filter(username=username).first()
            if obj is None:
                created += 1
                if not dry_run:
                    obj = User.objects.create(username=username, **defaults)
                    obj.set_password("ChangeMe123!")
                    obj.save(update_fields=["password"])
                self.stdout.write(self.style.SUCCESS(f"{'Would create' if dry_run else 'Created'} user: {username}"))
            else:
                changed = False
                for field, value in defaults.items():
                    if getattr(obj, field) != value:
                        setattr(obj, field, value)
                        changed = True
                if changed and not dry_run:
                    obj.save(update_fields=list(defaults.keys()))
                if changed:
                    updated += 1
                    self.stdout.write(self.style.WARNING(f"{'Would update' if dry_run else 'Updated'} user: {username}"))
            users[username] = obj

        self.stdout.write(f"Users: created={created}, updated={updated}, total={len(users)}")
        return users

    def _seed_custom_fields(self, dry_run=False):
        created = 0
        updated = 0
        skipped = 0
        for category_name, label, field_type, required, is_unique, select_options in CUSTOM_FIELDS:
            category = Category.objects.filter(name=category_name).first()
            if not category:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"Skipped custom field '{label}': category '{category_name}' not found"))
                continue

            obj = CustomFieldDefinition.objects.filter(category=category, label=label).first()
            if obj is None:
                created += 1
                if not dry_run:
                    CustomFieldDefinition.objects.create(
                        category=category,
                        label=label,
                        field_type=field_type,
                        required=required,
                        is_unique=is_unique,
                        select_options=select_options,
                    )
                self.stdout.write(self.style.SUCCESS(f"{'Would create' if dry_run else 'Created'} custom field: {category_name}::{label}"))
            else:
                changed = False
                if obj.field_type != field_type:
                    obj.field_type = field_type
                    changed = True
                if obj.required != required:
                    obj.required = required
                    changed = True
                if obj.is_unique != is_unique:
                    obj.is_unique = is_unique
                    changed = True
                if obj.select_options != select_options:
                    obj.select_options = select_options
                    changed = True
                if changed:
                    updated += 1
                    if not dry_run:
                        obj.save(update_fields=["field_type", "required", "is_unique", "select_options"])
                    self.stdout.write(self.style.WARNING(f"{'Would update' if dry_run else 'Updated'} custom field: {category_name}::{label}"))

        self.stdout.write(f"Custom fields: created={created}, updated={updated}, skipped={skipped}")

    def _seed_inventory(self, offices, dry_run=False):
        item_by_number = {}
        created = 0
        updated = 0

        for payload in ITEMS:
            category = Category.objects.get(name=payload["category"])
            office = offices[payload["office_code"]]
            defaults = {
                "title": payload["title"],
                "category": category,
                "office": office,
                "item_type": payload["item_type"],
                "status": payload["status"],
                "amount": payload["amount"],
                "price": payload["price"],
                "currency": payload["currency"],
                "department": payload["department"],
                "manufacturer": payload["manufacturer"],
                "purchased_date": payload["purchased_date"],
                "dynamic_data": payload["dynamic_data"],
            }

            obj = InventoryItem.objects.filter(item_number=payload["item_number"]).first()
            if obj is None:
                created += 1
                if not dry_run:
                    obj = InventoryItem.objects.create(item_number=payload["item_number"], **defaults)
                self.stdout.write(self.style.SUCCESS(f"{'Would create' if dry_run else 'Created'} item: {payload['item_number']}"))
            else:
                changed = False
                for field, value in defaults.items():
                    if getattr(obj, field) != value:
                        setattr(obj, field, value)
                        changed = True
                if changed:
                    updated += 1
                    if not dry_run:
                        obj.save(update_fields=list(defaults.keys()))
                    self.stdout.write(self.style.WARNING(f"{'Would update' if dry_run else 'Updated'} item: {payload['item_number']}"))

            if payload["item_type"] == InventoryItemType.FIXED_ASSET:
                fa_defaults = payload["fixed_asset"]
                if not dry_run and obj:
                    FixedAsset.objects.update_or_create(item=obj, defaults=fa_defaults)
            else:
                stock_defaults = payload["consumable_stock"]
                if not dry_run and obj:
                    ConsumableStock.objects.update_or_create(item=obj, defaults=stock_defaults)

            item_by_number[payload["item_number"]] = obj

        self.stdout.write(f"Inventory items: created={created}, updated={updated}, total={len(item_by_number)}")
        return item_by_number

    def _seed_assignments(self, items, users, offices, dry_run=False):
        assigned_item = items.get("FA-0001")
        returned_item = items.get("FA-0002")
        assigned_by = users.get("store_keeper")
        assigned_user = users.get("ward_officer_1")
        assigned_office = offices.get("NPL-L1-001")

        if not dry_run and assigned_item and assigned_by and assigned_user:
            ItemAssignment.objects.update_or_create(
                item=assigned_item,
                status=AssignmentStatus.ASSIGNED,
                defaults={
                    "assigned_to_user": assigned_user,
                    "assigned_to_office": None,
                    "assigned_by": assigned_by,
                    "handover_date": date(2025, 8, 1),
                    "assign_till": date(2026, 8, 1),
                    "handover_condition": ItemCondition.GOOD,
                    "remarks": "PRD seed: assigned laptop to ward officer",
                },
            )

        if not dry_run and returned_item and assigned_by and assigned_office:
            ItemAssignment.objects.update_or_create(
                item=returned_item,
                status=AssignmentStatus.RETURNED,
                defaults={
                    "assigned_to_user": None,
                    "assigned_to_office": assigned_office,
                    "assigned_by": assigned_by,
                    "handover_date": date(2025, 8, 12),
                    "assign_till": date(2025, 12, 31),
                    "returned_at": datetime(2025, 12, 20, 10, 30, tzinfo=timezone.utc),
                    "return_condition": ItemCondition.GOOD,
                    "handover_condition": ItemCondition.GOOD,
                    "remarks": "PRD seed: printer returned in good condition",
                },
            )

        self.stdout.write("Assignments: upserted 2 sample records")

    def _seed_stock_transactions(self, items, users, dry_run=False):
        if dry_run:
            self.stdout.write("Stock transactions: would upsert 2 sample records")
            return

        stock_item = items.get("CON-0001")
        performer = users.get("store_keeper")
        assignee = users.get("ward_officer_1")
        if not stock_item:
            self.stdout.write(self.style.WARNING("Stock transactions skipped: CON-0001 item not found"))
            return
        stock = ConsumableStock.objects.filter(item=stock_item).first()
        if not stock:
            self.stdout.write(self.style.WARNING("Stock transactions skipped: stock row for CON-0001 not found"))
            return

        in_txn, _ = ConsumableStockTransaction.objects.get_or_create(
            stock=stock,
            transaction_type=StockTransactionType.STOCK_IN,
            description="PRD seed opening stock adjustment",
            defaults={
                "quantity": Decimal("1000"),
                "balance_after": Decimal("1000"),
                "status": "COMPLETED",
                "amount": Decimal("10000"),
                "assigned_to": None,
                "performed_by": performer,
                "department": "Central Store",
            },
        )
        out_txn, _ = ConsumableStockTransaction.objects.get_or_create(
            stock=stock,
            transaction_type=StockTransactionType.STOCK_OUT,
            description="PRD seed issued to ward office",
            defaults={
                "quantity": Decimal("80"),
                "balance_after": Decimal("920"),
                "status": "COMPLETED",
                "amount": Decimal("800"),
                "assigned_to": assignee,
                "performed_by": performer,
                "department": "Ward Services",
            },
        )

        final_balance = out_txn.balance_after if out_txn else in_txn.balance_after
        if stock.quantity != final_balance:
            stock.quantity = final_balance
            stock.save(update_fields=["quantity"])

        self.stdout.write("Stock transactions: upserted 2 sample records")

    def _seed_audit_logs(self, items, users, dry_run=False):
        if dry_run:
            self.stdout.write("Audit logs: would upsert sample records")
            return

        actor = users.get("store_keeper")
        for item_number, item in items.items():
            if not item:
                continue
            InventoryAuditLog.objects.get_or_create(
                item=item,
                action_type=InventoryActionType.CREATE,
                remarks=f"PRD seed: created {item_number}",
                defaults={
                    "performed_by": actor,
                    "before_data": {},
                    "after_data": {
                        "item_number": item.item_number,
                        "title": item.title,
                        "status": item.status,
                        "item_type": item.item_type,
                    },
                },
            )

        assigned_item = items.get("FA-0001")
        returned_item = items.get("FA-0002")

        if assigned_item:
            InventoryAuditLog.objects.get_or_create(
                item=assigned_item,
                action_type=InventoryActionType.ASSIGN,
                remarks="PRD seed: assignment recorded",
                defaults={
                    "performed_by": actor,
                    "after_data": {"status": "ASSIGNED"},
                },
            )
        if returned_item:
            InventoryAuditLog.objects.get_or_create(
                item=returned_item,
                action_type=InventoryActionType.RETURN,
                remarks="PRD seed: return recorded",
                defaults={
                    "performed_by": actor,
                    "after_data": {"status": "RETURNED"},
                },
            )

        self.stdout.write("Audit logs: upserted sample records")

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
- `django_project/urls.py`
- `users/models.py`
- `hierarchy/models.py`
- `catalog/models.py`
- `inventory/models.py`
- `actions/models.py`
- `audit/models.py`
- `reports/views.py`
- `common/access.py`
- `common/management/commands/seed_prd_data.py`

