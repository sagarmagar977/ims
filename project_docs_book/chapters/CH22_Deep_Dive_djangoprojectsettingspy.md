# Chapter 22 — Deep Dive: `django_project/settings.py`

## Build Roadmap Position
- Stage: Deep Dive
- You are here: Chapter 22
- Before this: Chapter 21
- After this: Chapter 23

## Learning Objectives
- Read settings in execution order.
- Understand environment-driven behavior and production safeguards.
- `django_project/settings.py`

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 22 — Deep Dive: `django_project/settings.py`

## Learning Goals
- Read settings in execution order.
- Understand environment-driven behavior and production safeguards.

## Reference File
- `django_project/settings.py`

## Deep Dive Walkthrough

## 1) Environment helpers
- `_env_bool`, `_env_list` standardize env parsing.
- `_resolve_default_sqlite_path` finds writable SQLite fallback paths.
- `_database_from_url` parses PostgreSQL/SQLite URLs, including `sslmode`.

## 2) Core runtime toggles
- `IS_RENDER` derives Render environment.
- `HAS_CORSHEADERS` and `whitenoise` are feature-detected at import time.
- `DEBUG`, `ENABLE_SWAGGER`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` are env-driven.

## 3) App and middleware assembly
- Local apps + Django + DRF + schema tooling are registered.
- `corsheaders` and `whitenoise` are conditionally inserted.
- `common.middleware.LegacyApiDeprecationMiddleware` is always active.

## 4) Database and auth
- Uses `DATABASE_URL` when provided; else SQLite.
- `AUTH_USER_MODEL = "users.User"`.
- DRF defaults:
  - JWT auth,
  - authenticated access,
  - schema class,
  - filter/search/ordering backends,
  - page number pagination,
  - throttling classes/rates.

## 5) Static/media/security/email
- `STATIC_ROOT` set for deployment.
- WhiteNoise storage config enabled when package exists.
- `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL`, `LOW_STOCK_ALERT_EMAILS` read from env.
- In non-debug mode, strict checks enforce strong `SECRET_KEY`, configured hosts, and DB URL (unless temporary SQLite override).

## 6) CORS and docs metadata
- CORS options and optional `FRONTEND_URL` auto-append to allowed/trusted origins.
- `SPECTACULAR_SETTINGS` defines API title/description/version and Swagger UI behavior.

## What Is Missing in This File
- No Celery app configuration.
- No `CACHES` setting.

## Chapter 22 Outcome
You can now reason through settings load order and predict runtime behavior from environment variables.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
Not present in current project.

## Rebuild Step (Hands-on Roadmap)
- Implement or review the files listed in this chapter only.
- Validate behavior discussed in the original chapter explanation.
- Confirm readiness for the next chapter transition.

## Chapter Summary
This chapter ties repository explanation to exact code references and prepares the next build step.

## Files Used
- Not present in current project.

