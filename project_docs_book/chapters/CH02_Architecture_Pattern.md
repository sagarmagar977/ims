# Chapter 2 Architecture Pattern

## Build Roadmap Position
- Stage: Foundation
- You are here: Chapter 2
- Before this: Chapter 1
- After this: Chapter 3

## Learning Objectives
- Identify the architecture pattern implemented in this repository.
- Understand how responsibilities are split across Django apps.
- Distinguish global cross-cutting concerns from domain modules.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 2 Architecture Pattern

## Learning Goals
- Identify the architecture pattern implemented in this repository.
- Understand how responsibilities are split across Django apps.
- Distinguish global cross-cutting concerns from domain modules.

## Reference Files
- `django_project/settings.py`
- `django_project/urls.py`
- `common/permissions.py`
- `common/access.py`
- `common/middleware.py`
- `users/views.py`, `users/serializers.py`, `users/models.py`
- `inventory/views.py`, `inventory/serializers.py`, `inventory/models.py`
- `actions/views.py`, `audit/views.py`, `reports/views.py`

## Architecture Pattern Identified
The project uses a **modular monolith** architecture with **Django app-level domain segmentation**.

- Modular monolith:
  - One deployable backend service.
  - Multiple domain modules inside the same codebase and database.

- App-level segmentation:
  - `users` for identity/roles
  - `hierarchy` for office tree
  - `catalog` for category and custom fields
  - `inventory` for items/assets/consumable stock/stock transactions
  - `actions` for assignment workflows
  - `audit` for audit trail
  - `reports` for read/report/export endpoints
  - `common` for shared access, permission, and middleware concerns

## Request Handling Layering (Observed)
1. URL routing layer:
   - Root URL config includes each app router under `/api/` and `/api/v1/`.
2. View layer (DRF ViewSet/APIView):
   - Handles endpoints, filtering, ordering, permission checks, and custom actions.
3. Serializer layer:
   - Performs validation and data transformation.
   - In some cases performs transactional business logic (for example stock balance mutation in `ConsumableStockTransactionSerializer.create`).
4. Model layer:
   - Defines persistence schema, constraints, and entity-level integrity rules (`clean`, unique constraints, check constraints).
5. Database:
   - Default SQLite configuration; PostgreSQL supported via `DATABASE_URL`.

## Cross-Cutting Architecture Components
- Authentication and authorization:
  - Global DRF defaults enforce JWT authentication and authenticated access.
  - `IMSAccessPermission` applies role-based write/read policy.

- Data scope control:
  - `scope_queryset_by_user` filters querysets by office visibility rules (global vs scoped roles).

- API version transition strategy:
  - Middleware adds deprecation headers on legacy `/api/*` paths while `/api/v1/*` remains active.

## Architecture Characteristics
- Strengths observed:
  - Clear domain boundaries by Django app.
  - Consistent DRF patterns across modules.
  - Centralized permission and access-scope logic.
  - Built-in API version migration signaling.

- Tradeoffs observed:
  - No separate service/repository layer is present; some business logic lives in serializers/views.
  - Some dependencies in `requirements.txt` are not represented by visible runtime modules (for example Celery task modules are not present in scanned files).

## What Is Not Present (From Current Files)
- No microservice split.
- No separate frontend project in this repository.
- No dedicated event bus or message-driven workflow implementation in visible app code.

## Chapter 2 Outcome
You now have a concrete pattern map: this is a modular monolith Django REST system, organized by domain apps, with shared permission/scope middleware patterns and view-serializer-model request layering.
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

### File: `common/middleware.py`
```python
class LegacyApiDeprecationMiddleware:
    """
    Adds RFC-style deprecation metadata for legacy /api/* routes while /api/v1/* is active.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path or ""
        if path.startswith("/api/") and not path.startswith("/api/v1/"):
            response["Deprecation"] = "true"
            response["Sunset"] = "Wed, 31 Dec 2026 23:59:59 GMT"
            response["Link"] = '</api/v1/>; rel="successor-version"'
        return response

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

### File: `inventory/views.py`
```python
import csv
import io

from django.conf import settings
from django.core.mail import send_mail
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.models import InventoryActionType
from audit.utils import create_inventory_audit_log, item_snapshot
from common.access import scope_queryset_by_user
from common.permissions import IMSAccessPermission
from .models import ConsumableStock, ConsumableStockTransaction, FixedAsset, InventoryItem
from .serializers import (
    ConsumableStockSerializer,
    ConsumableStockTransactionSerializer,
    FixedAssetSerializer,
    InventoryItemSerializer,
)


class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.select_related("category", "office").all().order_by("id")
    serializer_class = InventoryItemSerializer
    filterset_fields = ["category", "office", "status", "item_type"]
    search_fields = ["title", "item_number", "category__name", "office__name"]
    ordering_fields = ["id", "title", "item_number", "created_at", "updated_at"]
    ordering = ["-created_at"]
    permission_classes = [IMSAccessPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        return scope_queryset_by_user(queryset, self.request.user, "office_id")

    def perform_create(self, serializer):
        item = serializer.save()
        create_inventory_audit_log(
            item=item,
            action_type=InventoryActionType.CREATE,
            user=self.request.user,
            after_data=item_snapshot(item),
            remarks="Inventory item created",
        )

    def perform_update(self, serializer):
        before = item_snapshot(self.get_object())
        item = serializer.save()
        create_inventory_audit_log(
            item=item,
            action_type=InventoryActionType.UPDATE,
            user=self.request.user,
            before_data=before,
            after_data=item_snapshot(item),
            remarks="Inventory item updated",
        )

    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

        decoded = file_obj.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))
        created_count = 0
        errors = []

        for index, row in enumerate(reader, start=2):
            payload = {
                "title": row.get("title"),
                "item_number": row.get("item_number") or None,
                "item_type": row.get("item_type"),
                "status": row.get("status"),
                "category": row.get("category"),
                "office": row.get("office"),
                "amount": row.get("amount") or 0,
                "price": row.get("price") or 0,
                "currency": row.get("currency") or "",
                "store": row.get("store") or "",
                "project": row.get("project") or "",
                "department": row.get("department") or "",
                "manufacturer": row.get("manufacturer") or "",
                "description": row.get("description") or "",
            }
            serializer = self.get_serializer(data=payload)
            if serializer.is_valid():
                item = serializer.save()
                create_inventory_audit_log(
                    item=item,
                    action_type=InventoryActionType.CREATE,
                    user=request.user,
                    after_data=item_snapshot(item),
                    remarks="Inventory item created (bulk import)",
                )
                created_count += 1
            else:
                errors.append({"line": index, "errors": serializer.errors})

        return Response(
            {"created": created_count, "failed": len(errors), "errors": errors},
            status=status.HTTP_200_OK,
        )


class FixedAssetViewSet(viewsets.ModelViewSet):
    queryset = FixedAsset.objects.select_related("item").all().order_by("id")
    serializer_class = FixedAssetSerializer
    filterset_fields = ["item"]
    search_fields = ["asset_tag", "serial_number", "item__title"]
    ordering_fields = ["id", "purchase_date", "warranty_expiry_date"]
    ordering = ["id"]
    permission_classes = [IMSAccessPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        return scope_queryset_by_user(queryset, self.request.user, "item__office_id")


class ConsumableStockViewSet(viewsets.ModelViewSet):
    queryset = ConsumableStock.objects.select_related("item").all().order_by("id")
    serializer_class = ConsumableStockSerializer
    filterset_fields = ["item", "reorder_alert_enabled"]
    search_fields = ["item__title", "unit"]
    ordering_fields = ["id", "quantity", "min_threshold"]
    ordering = ["id"]
    permission_classes = [IMSAccessPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        return scope_queryset_by_user(queryset, self.request.user, "item__office_id")


class ConsumableStockTransactionViewSet(viewsets.ModelViewSet):
    queryset = ConsumableStockTransaction.objects.select_related(
        "stock",
        "stock__item",
        "performed_by",
        "assigned_to",
    ).all().order_by("id")
    serializer_class = ConsumableStockTransactionSerializer
    filterset_fields = ["stock", "transaction_type", "status", "performed_by", "assigned_to"]
    search_fields = ["stock__item__title", "stock__item__item_number", "description", "department"]
    ordering_fields = ["id", "created_at", "quantity", "balance_after"]
    ordering = ["-created_at"]
    permission_classes = [IMSAccessPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        return scope_queryset_by_user(queryset, self.request.user, "stock__item__office_id")

    def perform_create(self, serializer):
        transaction_obj = serializer.save(performed_by=self.request.user)
        item = transaction_obj.stock.item
        action_type = InventoryActionType.UPDATE
        if transaction_obj.transaction_type == "STOCK_OUT":
            action_type = InventoryActionType.RETURN
        create_inventory_audit_log(
            item=item,
            action_type=action_type,
            user=self.request.user,
            after_data={
                "transaction_type": transaction_obj.transaction_type,
                "quantity": str(transaction_obj.quantity),
                "balance_after": str(transaction_obj.balance_after),
                "stock_id": transaction_obj.stock_id,
            },
            remarks="Consumable stock transaction",
        )

        stock = transaction_obj.stock
        if stock.reorder_alert_enabled and stock.quantity <= stock.min_threshold:
            recipients = [email for email in getattr(settings, "LOW_STOCK_ALERT_EMAILS", []) if email]
            if recipients:
                send_mail(
                    subject=f"Low stock alert: {stock.item.title}",
                    message=(
                        f"Item: {stock.item.title}\n"
                        f"Current quantity: {stock.quantity}\n"
                        f"Minimum threshold: {stock.min_threshold}\n"
                        f"Office: {stock.item.office.name}\n"
                    ),
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "ims@localhost"),
                    recipient_list=recipients,
                    fail_silently=True,
                )

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `actions/views.py`
```python
import csv
import io

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.models import InventoryActionType
from audit.utils import create_inventory_audit_log
from common.access import scope_queryset_by_user
from common.permissions import IMSAccessPermission
from .models import AssignmentStatus, ItemAssignment
from .serializers import ItemAssignmentSerializer


class ItemAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ItemAssignment.objects.select_related(
        "item",
        "assigned_to_user",
        "assigned_to_office",
        "assigned_by",
    ).all().order_by("id")
    serializer_class = ItemAssignmentSerializer
    filterset_fields = ["item", "assigned_to_user", "assigned_to_office", "status", "assign_till"]
    search_fields = ["item__title", "item__item_number", "assigned_to_user__username", "assigned_to_office__name", "remarks"]
    ordering_fields = ["id", "handover_date", "assign_till", "created_at", "returned_at"]
    ordering = ["-created_at"]
    permission_classes = [IMSAccessPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        return scope_queryset_by_user(queryset, self.request.user, "item__office_id")

    def perform_create(self, serializer):
        assignment = serializer.save(assigned_by=self.request.user)
        create_inventory_audit_log(
            item=assignment.item,
            action_type=InventoryActionType.ASSIGN,
            user=self.request.user,
            after_data={
                "assignment_id": assignment.id,
                "assigned_to_user": assignment.assigned_to_user_id,
                "assigned_to_office": assignment.assigned_to_office_id,
                "status": assignment.status,
                "assign_till": assignment.assign_till.isoformat() if assignment.assign_till else None,
            },
            remarks="Item assigned",
        )

    def perform_update(self, serializer):
        before_instance = self.get_object()
        before = {
            "status": before_instance.status,
            "assigned_to_user": before_instance.assigned_to_user_id,
            "assigned_to_office": before_instance.assigned_to_office_id,
            "returned_at": before_instance.returned_at.isoformat() if before_instance.returned_at else None,
        }
        assignment = serializer.save()
        action_type = InventoryActionType.RETURN if assignment.status == AssignmentStatus.RETURNED else InventoryActionType.ASSIGN
        create_inventory_audit_log(
            item=assignment.item,
            action_type=action_type,
            user=self.request.user,
            before_data=before,
            after_data={
                "status": assignment.status,
                "assigned_to_user": assignment.assigned_to_user_id,
                "assigned_to_office": assignment.assigned_to_office_id,
                "returned_at": assignment.returned_at.isoformat() if assignment.returned_at else None,
            },
            remarks="Item assignment updated",
        )

    @action(detail=False, methods=["get"], url_path="summary-by-assignee")
    def summary_by_assignee(self, request):
        today = timezone.now().date()
        scoped_qs = scope_queryset_by_user(ItemAssignment.objects.all(), request.user, "item__office_id")
        data = list(
            scoped_qs.values(
                "assigned_to_user",
                "assigned_to_user__first_name",
                "assigned_to_user__last_name",
                "assigned_to_user__username",
                "assigned_to_office",
                "assigned_to_office__name",
            )
            .annotate(
                total_items=Count("id"),
                active=Count("id", filter=Q(status=AssignmentStatus.ASSIGNED)),
                overdue=Count(
                    "id",
                    filter=Q(status=AssignmentStatus.ASSIGNED, assign_till__lt=today),
                ),
                returned=Count("id", filter=Q(status=AssignmentStatus.RETURNED)),
            )
            .order_by("assigned_to_user__username", "assigned_to_office__name")
        )
        return Response(data)

    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

        decoded = file_obj.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))
        created_count = 0
        errors = []

        for index, row in enumerate(reader, start=2):
            payload = {
                "item": row.get("item"),
                "assigned_to_user": row.get("assigned_to_user") or None,
                "assigned_to_office": row.get("assigned_to_office") or None,
                "handover_date": row.get("handover_date"),
                "assign_till": row.get("assign_till") or None,
                "handover_condition": row.get("handover_condition") or "GOOD",
                "status": row.get("status") or "ASSIGNED",
                "remarks": row.get("remarks") or "",
            }
            serializer = self.get_serializer(data=payload)
            if serializer.is_valid():
                assignment = serializer.save(assigned_by=request.user)
                create_inventory_audit_log(
                    item=assignment.item,
                    action_type=InventoryActionType.ASSIGN,
                    user=request.user,
                    after_data={
                        "assignment_id": assignment.id,
                        "assigned_to_user": assignment.assigned_to_user_id,
                        "assigned_to_office": assignment.assigned_to_office_id,
                        "status": assignment.status,
                        "assign_till": assignment.assign_till.isoformat() if assignment.assign_till else None,
                    },
                    remarks="Item assigned (bulk import)",
                )
                created_count += 1
            else:
                errors.append({"line": index, "errors": serializer.errors})

        return Response(
            {"created": created_count, "failed": len(errors), "errors": errors},
            status=status.HTTP_200_OK,
        )

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
- `common/permissions.py`
- `common/access.py`
- `common/middleware.py`
- `users/views.py`
- `inventory/views.py`
- `actions/views.py`

