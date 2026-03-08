# Chapter 19 — Common App Files

## Learning Goals
- Understand shared permission and data-scope rules.
- Trace middleware behavior for API deprecation signaling.
- Learn bootstrap/seed command responsibilities.

## Reference Files
- `common/access.py`
- `common/permissions.py`
- `common/middleware.py`
- `common/views.py`
- `common/models.py`
- `common/tests.py`
- `common/admin.py`
- `common/apps.py`
- `common/management/commands/bootstrap_admin.py`
- `common/management/commands/seed_prd_data.py`

## File Breakdown

## 1) `common/permissions.py`
- Defines role sets:
  - read-only: `FINANCE`, `AUDIT`
  - write-capable baseline roles
- `WRITE_ROLE_MATRIX` maps viewset basename to allowed write roles.
- `IMSAccessPermission`:
  - allows staff/superuser,
  - allows authenticated reads,
  - denies writes for read-only roles,
  - enforces per-resource role matrix for writes.

## 2) `common/access.py`
- `get_descendant_office_ids(root_office_id)`: iterative traversal of office tree.
- `get_accessible_office_ids(user)`:
  - global roles and staff/superuser => unrestricted (`None`),
  - scoped roles => office subtree (or own office for ward),
  - others => empty list.
- `scope_queryset_by_user(queryset, user, office_lookup)` applies filtered office visibility.

## 3) `common/middleware.py`
- `LegacyApiDeprecationMiddleware` adds headers on `/api/*` (excluding `/api/v1/*`):
  - `Deprecation: true`
  - `Sunset: Wed, 31 Dec 2026 23:59:59 GMT`
  - `Link: </api/v1/>; rel="successor-version"`

## 4) Management commands
- `bootstrap_admin.py`:
  - creates/updates bootstrap admin from env vars,
  - sets staff/superuser flags and optional `role`.
- `seed_prd_data.py`:
  - idempotently seeds offices, users, custom fields, inventory, assignments, transactions, audit logs,
  - supports `--dry-run` with transaction rollback,
  - invokes `seed_initial_categories`.

## 5) Remaining common files
- `common/models.py`: placeholder only.
- `common/views.py`: placeholder only.
- `common/admin.py`: placeholder only.
- `common/apps.py`: defines `CommonConfig`.
- `common/tests.py`: verifies deprecation headers appear on `/api/*` and not on `/api/v1/*`.

## Chapter 19 Outcome
You now have the cross-cutting control map: RBAC, office scoping, API deprecation signaling, and bootstrap/seed automation.
