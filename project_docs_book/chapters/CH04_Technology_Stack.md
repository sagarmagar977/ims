# Chapter 4 — Technology Stack

## Build Roadmap Position
- Stage: Foundation
- You are here: Chapter 4
- Before this: Chapter 3
- After this: Chapter 5

## Learning Objectives
- Identify the exact technologies used in this backend.
- Separate actively configured stack components from dependency-only entries.
- Understand runtime, API, data, and reporting tool choices.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 4 — Technology Stack

## Learning Goals
- Identify the exact technologies used in this backend.
- Separate actively configured stack components from dependency-only entries.
- Understand runtime, API, data, and reporting tool choices.

## Reference Files
- `requirements.txt`
- `django_project/settings.py`
- `render.yaml`
- `Procfile`
- `gunicorn.conf.py`

## Core Runtime Stack
- Python runtime:
  - Render config sets `PYTHON_VERSION=3.12.8`.
- Web framework:
  - `Django==6.0.2`
- API framework:
  - `djangorestframework==3.16.1`

## API and Auth Stack
- JWT authentication:
  - `djangorestframework_simplejwt==5.5.1`
  - DRF default auth class is `JWTAuthentication`.
- Filtering/search/ordering:
  - `django-filter==25.2`
  - DRF filter backends include DjangoFilterBackend + SearchFilter + OrderingFilter.
- API schema/docs:
  - `drf-spectacular==0.29.0`
  - OpenAPI schema + Swagger UI endpoints are configured.
- Throttling and pagination:
  - DRF built-in throttles (`AnonRateThrottle`, `UserRateThrottle`) and page-number pagination.

## Data and Storage Stack
- ORM/database layer:
  - Django ORM.
- Local/default DB:
  - SQLite (`django.db.backends.sqlite3`).
- Production-capable DB driver:
  - `psycopg2-binary==2.9.11` for PostgreSQL via `DATABASE_URL`.
- File/static handling:
  - `whitenoise==6.9.0` is conditionally used if installed.
  - `django-storages==1.14.6` is present in dependencies.

## Reporting and Export Stack
- Excel export:
  - `openpyxl==3.1.5`
- PDF export:
  - `reportlab==4.4.10`
- Additional PDF dependency present:
  - `pypdf==6.7.3`

## Deployment and Serving Stack
- Process server:
  - `gunicorn==23.0.0` with config in `gunicorn.conf.py`.
- Deployment targets present:
  - Render via `render.yaml`.
  - Procfile-based process startup via `Procfile`.
- Startup flow (as configured):
  - run migrations,
  - collect static files,
  - bootstrap admin on Render,
  - start Gunicorn with WSGI app.

## CORS and Security Configuration
- Optional CORS middleware support:
  - `corsheaders` is conditionally imported if available.
- Security config in production mode includes:
  - SSL redirect,
  - secure cookies,
  - HSTS,
  - host/secret/db validation checks.

## Dependency Groups Present but Not Wired in Visible App Code
From `requirements.txt`, these packages are present, but explicit runtime modules were not found in scanned project app files:
- Celery ecosystem: `celery`, `amqp`, `billiard`, `kombu`, `vine`, `redis`, `click-*`
- This indicates dependency presence; actual task/worker module setup is not visible in the current repository scan.

## Technology Stack Summary
The confirmed stack is Django + DRF + JWT + PostgreSQL-capable ORM backend, served by Gunicorn, documented with drf-spectacular, with export/reporting via openpyxl and reportlab, and deployable through Render/Procfile workflows.

## Chapter 4 Outcome
You now have an exact, evidence-based stack map showing what is configured and what is only dependency-level presence.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
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

## Rebuild Step (Hands-on Roadmap)
- Implement or review the files listed in this chapter only.
- Validate behavior discussed in the original chapter explanation.
- Confirm readiness for the next chapter transition.

## Chapter Summary
This chapter ties repository explanation to exact code references and prepares the next build step.

## Files Used
- `requirements.txt`
- `django_project/settings.py`
- `render.yaml`
- `Procfile`
- `gunicorn.conf.py`

