# Chapter 11 — Core Runtime & Deployment Files

## Build Roadmap Position
- Stage: Core Domain
- You are here: Chapter 11
- Before this: Chapter 10
- After this: Chapter 12

## Learning Objectives
- Understand the purpose of each runtime and deployment core file.
- Trace how these files work together from command execution to live service.
- Identify operational responsibilities and boundaries of each file.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 11 — Core Runtime & Deployment Files

## Learning Goals
- Understand the purpose of each runtime and deployment core file.
- Trace how these files work together from command execution to live service.
- Identify operational responsibilities and boundaries of each file.

## Reference Files
- `manage.py`
- `django_project/settings.py`
- `django_project/urls.py`
- `django_project/asgi.py`
- `django_project/wsgi.py`
- `gunicorn.conf.py`
- `Procfile`
- `render.yaml`
- `.smoke_test.py`

## File-by-File Breakdown

## 1) `manage.py`
Role:
- CLI runtime entrypoint for Django management commands.

Core behavior:
- Sets `DJANGO_SETTINGS_MODULE=django_project.settings`.
- Calls `execute_from_command_line(sys.argv)`.

Operational use:
- local development commands (`runserver`, `migrate`, etc.)
- deployment pre-start commands (`migrate`, `collectstatic`, `bootstrap_admin`)

## 2) `django_project/settings.py`
Role:
- Central runtime configuration contract.

Core responsibilities:
- environment parsing helpers (`_env_bool`, `_env_list`, database URL parser)
- app and middleware registration
- database selection (SQLite default, PostgreSQL via `DATABASE_URL`)
- DRF auth/permission/filter/pagination/throttle defaults
- static storage setup (conditional WhiteNoise integration)
- security settings for non-debug mode
- CORS/CSRF frontend-origin settings
- schema metadata for drf-spectacular

Operational importance:
- This file defines global runtime behavior and security posture.

## 3) `django_project/urls.py`
Role:
- Root request dispatch table.

Core responsibilities:
- registers admin and health routes
- registers JWT token routes
- registers schema/docs routes
- includes all domain app routes under `/api/` and `/api/v1/`

Operational importance:
- single source of top-level API entrypoints and versioned route composition.

## 4) `django_project/asgi.py`
Role:
- ASGI application entrypoint.

Core behavior:
- sets settings module
- exposes `application = get_asgi_application()`

Operational note:
- present and valid, but current deployment commands in repository use WSGI/Gunicorn path.

## 5) `django_project/wsgi.py`
Role:
- WSGI application entrypoint.

Core behavior:
- sets settings module
- exposes `application = get_wsgi_application()`

Operational note:
- this is the active deployment app target used by Gunicorn commands.

## 6) `gunicorn.conf.py`
Role:
- process server runtime tuning for production serving.

Configured controls:
- bind host/port
- worker count and worker class
- timeout/graceful timeout/keepalive
- max requests + jitter
- log routing and log level

Operational importance:
- controls stability and throughput characteristics of the live process.

## 7) `Procfile`
Role:
- process declaration for Procfile-compatible platforms.

Configured web command:
- migrate
- collect static files
- start Gunicorn with WSGI application

Operational importance:
- compact deployment startup contract.

## 8) `render.yaml`
Role:
- Render platform deployment manifest.

Configured responsibilities:
- service metadata (`type`, `env`, `plan`)
- build command (`pip install` + `collectstatic`)
- start command (`migrate` + `bootstrap_admin` + gunicorn)
- health check endpoint (`/health/`)
- key environment variables (`PYTHON_VERSION`, `DEBUG`, `SECRET_KEY`, hosts/origins)

Operational importance:
- codifies environment and startup behavior for Render deployments.

## 9) `.smoke_test.py`
Role:
- post-setup sanity script for API behavior.

Observed flow:
- ensures admin user exists
- authenticates via token endpoint
- exercises representative APIs (dashboard, inventory create, assignment, stock transaction, logs)

Operational importance:
- lightweight verification of key runtime pathways.

## Runtime & Deployment Interaction Chain
```text
Deployment command (Procfile/render)
-> manage.py pre-run tasks (migrate/collectstatic/bootstrap)
-> gunicorn (gunicorn.conf.py)
-> django_project.wsgi:application
-> settings load
-> urls dispatch
-> app endpoints
```

## What Is Not Present
- No ASGI server startup command in deployment files.
- No separate worker process command in Procfile/render manifest.

## Chapter 11 Outcome
You now have a clear operational map of the core runtime and deployment files, including each file’s role and how they combine into the full service startup chain.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
### File: `manage.py`
```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

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

### File: `django_project/asgi.py`
```python
"""
ASGI config for django_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')

application = get_asgi_application()

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `django_project/wsgi.py`
```python
"""
WSGI config for django_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')

application = get_wsgi_application()

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `gunicorn.conf.py`
```python
import multiprocessing
import os


bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv("WEB_CONCURRENCY", max((multiprocessing.cpu_count() * 2) + 1, 2)))
worker_class = "sync"
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "100"))

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

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

### File: `.smoke_test.py`
```python
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from catalog.models import Category
from hierarchy.models import Office, OfficeLevels
from inventory.models import InventoryItem

User = get_user_model()
admin, created = User.objects.get_or_create(username='admin', defaults={'email':'admin@example.com'})
if created:
    admin.is_staff = True
    admin.is_superuser = True
    admin.set_password('admin123')
    admin.save()
else:
    admin.set_password('admin123')
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()

office, _ = Office.objects.get_or_create(name='Central Office', defaults={'level': OfficeLevels.CENTRAL, 'location_code': 'CENTRAL-001'})
if office.level != OfficeLevels.CENTRAL:
    office.level = OfficeLevels.CENTRAL
    office.location_code = office.location_code or 'CENTRAL-001'
    office.save()

laptop_cat, _ = Category.objects.get_or_create(name='Laptop', defaults={'is_consumable': False})
toner_cat, _ = Category.objects.get_or_create(name='Toner', defaults={'is_consumable': True})

client = APIClient()
resp = client.post('/api/auth/token/', {'username':'admin','password':'admin123'}, format='json')
print('token status', resp.status_code)
assert resp.status_code == 200, resp.content
access = resp.data['access']
client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

print('dashboard status', client.get('/api/reports/dashboard-summary/').status_code)
print('recent activities status', client.get('/api/reports/recent-inventory-activities/').status_code)

item_payload = {
    'title': 'Laptop - Dell 5420',
    'item_number': 'ITM-0001',
    'item_type': 'FIXED_ASSET',
    'status': 'ACTIVE',
    'category': laptop_cat.id,
    'office': office.id,
    'amount': '1',
    'price': '1200.00',
    'currency': 'NPR'
}
item_resp = client.post('/api/inventory-items/', item_payload, format='json')
print('create item status', item_resp.status_code)
if item_resp.status_code not in (200, 201):
    print(item_resp.data)

item = InventoryItem.objects.filter(item_number='ITM-0001').first()
if item:
    assign_resp = client.post('/api/item-assignments/', {
        'item': item.id,
        'assigned_to_user': admin.id,
        'handover_date': '2026-02-25',
        'assign_till': '2026-03-25',
        'status': 'ASSIGNED'
    }, format='json')
    print('create assignment status', assign_resp.status_code)
    if assign_resp.status_code not in (200, 201):
        print(assign_resp.data)

cons_payload = {
    'title': 'Toner Cartridge',
    'item_number': 'CON-0001',
    'item_type': 'CONSUMABLE',
    'status': 'ACTIVE',
    'category': toner_cat.id,
    'office': office.id,
    'amount': '1'
}
cons_resp = client.post('/api/inventory-items/', cons_payload, format='json')
print('create consumable item status', cons_resp.status_code)
if cons_resp.status_code not in (200, 201):
    print(cons_resp.data)

cons_item = InventoryItem.objects.filter(item_number='CON-0001').first()
if cons_item:
    stock_resp = client.post('/api/consumable-stocks/', {
        'item': cons_item.id,
        'initial_quantity': '100',
        'quantity': '100',
        'min_threshold': '20',
        'unit': 'pcs'
    }, format='json')
    print('create stock status', stock_resp.status_code)
    if stock_resp.status_code not in (200, 201):
        print(stock_resp.data)
    if stock_resp.status_code in (200, 201):
        tx_resp = client.post('/api/consumable-stock-transactions/', {
            'stock': stock_resp.data['id'],
            'transaction_type': 'STOCK_OUT',
            'quantity': '5',
            'status': 'ON_BOARDED',
            'amount': '5',
            'department': 'Stores',
            'description': 'Issue to office'
        }, format='json')
        print('create stock tx status', tx_resp.status_code)
        if tx_resp.status_code not in (200, 201):
            print(tx_resp.data)

print('assignee summary status', client.get('/api/item-assignments/summary-by-assignee/').status_code)
print('audit logs status', client.get('/api/audit-logs/').status_code)
print('stock transactions list status', client.get('/api/consumable-stock-transactions/').status_code)

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
- `manage.py`
- `django_project/settings.py`
- `django_project/urls.py`
- `django_project/asgi.py`
- `django_project/wsgi.py`
- `gunicorn.conf.py`
- `Procfile`
- `render.yaml`
- `.smoke_test.py`

