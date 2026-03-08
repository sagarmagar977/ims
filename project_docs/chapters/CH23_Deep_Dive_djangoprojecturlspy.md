# Chapter 23 — Deep Dive: `django_project/urls.py`

## Learning Goals
- Understand top-level URL composition and version strategy.
- Trace auth/docs/health and app route inclusion.

## Reference File
- `django_project/urls.py`

## Deep Dive Walkthrough

## 1) Core routes
- `/admin/` -> Django admin.
- `/health/` -> JSON `{"status": "ok"}`.

## 2) Auth routes
- Legacy and versioned JWT endpoints both exist:
  - `/api/auth/token/`, `/api/auth/token/refresh/`
  - `/api/v1/auth/token/`, `/api/v1/auth/token/refresh/`

## 3) Schema/docs routes
- Legacy and v1 schema/docs both exposed:
  - `/api/schema/`, `/api/docs/`
  - `/api/v1/schema/`, `/api/v1/docs/`

## 4) App route inclusion
- For `/api/` and `/api/v1/`, the same app URL modules are included:
  - `users`, `hierarchy`, `catalog`, `inventory`, `actions`, `audit`, `reports`.

## 5) Versioning implications
- Dual prefix inclusion means both legacy and v1 route families are active.
- `LegacyApiDeprecationMiddleware` (in settings middleware) marks `/api/*` responses with deprecation headers.

## Chapter 23 Outcome
You now understand exactly how request paths are dispatched at the project root and why both API generations currently coexist.
