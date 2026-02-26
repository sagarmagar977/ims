# Local to Railway Hosting Transition

This document summarizes the changes made to move the IMS backend from local hosting to Railway hosting.

## Scope
- Project: IMS Django backend
- Goal: Production-ready deployment on Railway via GitHub
- Date: 2026-02-26

## What Changed

### 1. Environment-based production settings
Updated [django_project/settings.py](x:/mindrisers/projects/ims/django_project/settings.py) to avoid hardcoded local/dev assumptions.

Key changes:
- `DEBUG` now comes from environment (`DEBUG`).
- `SECRET_KEY` now comes from environment (`SECRET_KEY`).
- `ALLOWED_HOSTS` now comes from environment (`ALLOWED_HOSTS`).
- `CSRF_TRUSTED_ORIGINS` now comes from environment (`CSRF_TRUSTED_ORIGINS`).
- Auto-append `RAILWAY_PUBLIC_DOMAIN` to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` when present.

### 2. Database configuration for Railway
- Added `DATABASE_URL` support in settings.
- If `DATABASE_URL` exists, Django uses PostgreSQL configuration parsed from it.
- If missing, app falls back to SQLite (local/dev path).
- Added production guard to require `DATABASE_URL` when `DEBUG=False` unless `ALLOW_SQLITE_IN_PROD=true`.

### 3. Static files for production
- Configured:
  - `STATIC_URL = "/static/"`
  - `STATIC_ROOT = BASE_DIR / "staticfiles"`
- Added WhiteNoise support (enabled when package exists):
  - Middleware injection
  - `CompressedManifestStaticFilesStorage`

### 4. Railway startup/runtime configuration
Added:
- [Procfile](x:/mindrisers/projects/ims/Procfile)
- [railway.json](x:/mindrisers/projects/ims/railway.json)

Startup command now runs:
1. `python manage.py migrate`
2. `python manage.py collectstatic --noinput`
3. `gunicorn django_project.wsgi:application --bind 0.0.0.0:$PORT`

### 5. Runtime dependencies
Updated [requirements.txt](x:/mindrisers/projects/ims/requirements.txt):
- Added `gunicorn`
- Added `whitenoise`

### 6. Production hardening
When `DEBUG=False`, settings now enforce:
- Secure cookies (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`)
- SSL redirect (`SECURE_SSL_REDIRECT`)
- HSTS settings (`SECURE_HSTS_*`)
- `SECURE_CONTENT_TYPE_NOSNIFF = True`
- `SECURE_REFERRER_POLICY = "same-origin"`
- `X_FRAME_OPTIONS = "DENY"`
- Proxy headers for Railway (`SECURE_PROXY_SSL_HEADER`, `USE_X_FORWARDED_HOST`)

Also added startup guards:
- Reject weak/default `SECRET_KEY` in production.
- Reject default/empty `ALLOWED_HOSTS` in production.

### 7. Swagger docs toggle
Updated [django_project/urls.py](x:/mindrisers/projects/ims/django_project/urls.py):
- Swagger/schema endpoints are now conditional on `ENABLE_SWAGGER`.
- Recommended in production: `ENABLE_SWAGGER=false`.

## Railway Environment Variables

Set these in Railway service variables:

- `DEBUG=False`
- `SECRET_KEY=<long-random-secret>`
- `DATABASE_URL=<auto-provided-by-Railway-Postgres>`
- `ALLOWED_HOSTS=<your-service>.up.railway.app`
- `CSRF_TRUSTED_ORIGINS=https://<your-service>.up.railway.app`
- `ENABLE_SWAGGER=false` (recommended)

Optional:
- `SECURE_SSL_REDIRECT=true`
- `SECURE_HSTS_SECONDS=31536000`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS=true`
- `SECURE_HSTS_PRELOAD=true`

## Deployment Flow (GitHub -> Railway)

1. Push code changes to GitHub.
2. In Railway, create project from GitHub repo.
3. Add PostgreSQL plugin/service.
4. Confirm `DATABASE_URL` is injected into web service.
5. Set env vars listed above.
6. Trigger deploy.
7. Validate:
   - Health path from `railway.json`: `/api/schema/` (if `ENABLE_SWAGGER=true`)
   - JWT token endpoint: `/api/auth/token/`

## Notes / Known Non-Blocking Warnings

- drf-spectacular schema warnings remain for some APIViews in reports module.
- These warnings affect OpenAPI docs quality, not API runtime stability.

## Quick Verification Checklist

- [ ] App boots on Railway without config errors.
- [ ] Migrations run successfully.
- [ ] Static collection succeeds.
- [ ] Login token endpoint works.
- [ ] Core API endpoints return expected data.
- [ ] HTTPS works and no host/csrf errors in browser/API client.

