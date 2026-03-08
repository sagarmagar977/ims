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
