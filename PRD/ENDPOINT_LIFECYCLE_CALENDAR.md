# Endpoint Lifecycle and Deprecation Calendar

## Scope
- Legacy API prefix: `/api/`
- Successor API prefix: `/api/v1/`

## Calendar
- Deprecation effective date: `2026-03-08`
- Sunset date: `2026-12-31` (HTTP `Sunset` header: `Thu, 31 Dec 2026 23:59:59 GMT`)
- CI enforcement start date: `2027-01-01`

## Lifecycle Stages
1. Active: Endpoint family is fully supported.
2. Deprecated: Endpoint keeps serving traffic and always returns `Deprecation: true`, `Sunset`, and `Link` headers.
3. Sunset reached: Legacy endpoint is still callable until enforcement date, but removal is mandatory.
4. Removed: Legacy route must be deleted; CI fails if still present.

## Endpoint Families Covered
- `users.urls`
- `hierarchy.urls`
- `catalog.urls`
- `inventory.urls`
- `actions.urls`
- `audit.urls`
- `reports.urls`
- `common.urls`

## CI Enforcement Rules
- Calendar file must remain date-valid and chronological.
- Middleware sunset header must match calendar sunset date.
- Every listed module must be mounted in both `/api/` and `/api/v1/` before enforcement.
- On and after `2027-01-01`, no listed module may remain under `/api/`.
