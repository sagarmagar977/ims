# Chapter 10 — External Integrations

## Build Roadmap Position
- Stage: Execution Flow
- You are here: Chapter 10
- Before this: Chapter 9
- After this: Chapter 11

## Learning Objectives
- Identify all external integration points present in this backend.
- Distinguish actively wired integrations from dependency-only presence.
- Understand integration configuration surfaces (settings, env vars, deployment files).

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 10 — External Integrations

## Learning Goals
- Identify all external integration points present in this backend.
- Distinguish actively wired integrations from dependency-only presence.
- Understand integration configuration surfaces (settings, env vars, deployment files).

## Reference Files
- `django_project/settings.py`
- `django_project/urls.py`
- `inventory/views.py`
- `reports/views.py`
- `render.yaml`
- `Procfile`
- `requirements.txt`

## Integration Categories Found
1. Authentication integration (JWT)
2. API schema/documentation integration
3. Email integration
4. Database integration
5. Deployment/platform integration
6. Reverse-proxy and frontend-origin integration
7. Reporting/export library integration

## 1) Authentication Integration
- Package: `djangorestframework_simplejwt`
- Config: DRF default auth class uses JWT authentication.
- Endpoints exposed:
  - `/api/auth/token/`
  - `/api/auth/token/refresh/`
  - versioned equivalents under `/api/v1/`.

Integration role:
- External clients authenticate using bearer tokens issued by JWT endpoints.

## 2) API Schema & Docs Integration
- Package: `drf-spectacular`
- Endpoints:
  - `/api/schema/`, `/api/docs/`
  - `/api/v1/schema/`, `/api/v1/docs/`

Integration role:
- External consumers can discover and test the API contract.

## 3) Email Integration
- Config keys:
  - `EMAIL_BACKEND`
  - `DEFAULT_FROM_EMAIL`
  - `LOW_STOCK_ALERT_EMAILS`
- Runtime usage:
  - `inventory.views.ConsumableStockTransactionViewSet.perform_create` calls `send_mail(...)` for low-stock alerts.

Integration role:
- Outbound notification channel for stock threshold events.

## 4) Database Integration
- Config input:
  - `DATABASE_URL` parsed to PostgreSQL or SQLite connection settings.
- Default path:
  - SQLite local DB when `DATABASE_URL` not set.
- Production-capable driver present:
  - `psycopg2-binary`.

Integration role:
- Persistent storage boundary with environment-driven engine selection.

## 5) Deployment/Platform Integration
- Render integration:
  - `render.yaml` defines build/start commands, env vars, and health check path.
- Procfile process integration:
  - `Procfile` defines `web` process command.
- Runtime server integration:
  - Gunicorn startup with `gunicorn.conf.py`.

Integration role:
- Connects app lifecycle to hosting platform process model.

## 6) Frontend-Origin / Proxy Integration
- Proxy-aware settings:
  - `SECURE_PROXY_SSL_HEADER`, `USE_X_FORWARDED_HOST`.
- Origin/CORS integration:
  - `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`.
  - Optional `corsheaders` middleware when package is installed.

Integration role:
- Enables browser-based frontend communication from separate host/domain.

## 7) Reporting/Export Integrations
- Excel export library: `openpyxl`
- PDF export library: `reportlab`
- Implemented in report export views for downloadable artifacts.

Integration role:
- External file-format interfaces for downstream reporting users/tools.

## Dependency-Only or Not-Wired Integrations
From `requirements.txt`, these ecosystems are present but not visibly wired in app runtime/deployment code scanned:
- Celery/Redis stack (`celery`, `redis`, `amqp`, `kombu`, etc.)
- No deployment worker command or task module was found in current files.

## Not Present in Current Repository
- No explicit third-party HTTP API client integration in app code (for example external SaaS API calls).
- No webhook consumer integration modules detected.

## Integration Risk/Control Notes
- Most integrations are env-driven, so behavior depends on deployment configuration.
- Email integration uses `fail_silently=True` in low-stock send path.
- Security and host/origin integration checks tighten when `DEBUG` is false.

## Chapter 10 Outcome
You now have a verified integration map showing exactly which external interfaces are active, configurable, optional, or currently not wired in this project.
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

### File: `render.yaml`
```yaml
services:
  - type: web
    name: ims-backend
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt && python manage.py collectstatic --noinput
    startCommand: python manage.py migrate && python manage.py bootstrap_admin && gunicorn -c gunicorn.conf.py django_project.wsgi:application
    healthCheckPath: /health/
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.8
      - key: DEBUG
        value: "False"
      - key: SECRET_KEY
        generateValue: true
      - key: ALLOWED_HOSTS
        value: .onrender.com
      - key: CSRF_TRUSTED_ORIGINS
        value: https://*.onrender.com
      - key: ENABLE_SWAGGER
        value: "true"
      - key: FRONTEND_URL
        sync: false 
      

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `Procfile`
```text
web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn -c gunicorn.conf.py django_project.wsgi:application

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `requirements.txt`
```text
amqp==5.3.1
asgiref==3.11.1
attrs==25.4.0
billiard==4.2.4
celery==5.6.2
charset-normalizer==3.4.4
click==8.3.1
click-didyoumean==0.3.1
click-plugins==1.1.1.2
click-repl==0.3.0
colorama==0.4.6
Django==6.0.2
django-filter==25.2
django-storages==1.14.6
djangorestframework==3.16.1
djangorestframework_simplejwt==5.5.1
drf-spectacular==0.29.0
et_xmlfile==2.0.0
gunicorn==23.0.0
whitenoise==6.9.0
inflection==0.5.1
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
kombu==5.6.2
openpyxl==3.1.5
packaging==26.0
pillow==12.1.1
prompt_toolkit==3.0.52
psycopg2-binary==2.9.11
PyJWT==2.11.0
pypdf==6.7.3
python-dateutil==2.9.0.post0
PyYAML==6.0.3
redis==7.2.0
referencing==0.37.0
reportlab==4.4.10
rpds-py==0.30.0
six==1.17.0
sqlparse==0.5.5
tzdata==2025.3
tzlocal==5.3.1
uritemplate==4.2.0
vine==5.1.0
wcwidth==0.6.0

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
- `inventory/views.py`
- `reports/views.py`
- `render.yaml`
- `Procfile`
- `requirements.txt`

