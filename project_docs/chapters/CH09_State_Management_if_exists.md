# Chapter 9 — State Management (if exists)

## Learning Goals
- Identify what "state" is managed in this backend.
- Distinguish persistent state, auth state, and request-scoped derived state.
- Confirm which common state-management patterns are not present.

## Reference Files
- `django_project/settings.py`
- `users/models.py`
- `inventory/models.py`
- `actions/models.py`
- `audit/models.py`
- `common/access.py`
- `common/permissions.py`

## State Management Exists: Yes (Backend-Persistent + Request-Derived)
This project manages state primarily through:
1. Database-backed domain state (Django models)
2. JWT-based authentication state
3. Request-time derived access scope state
4. Audit timeline state

## 1) Persistent Domain State (Primary)
State is persisted in relational tables via Django models.

Key persistent state groups:
- User and role state:
  - `users.User` with `role`, `office`, and standard auth fields.
- Inventory lifecycle state:
  - `InventoryItem.status` (`ACTIVE`, `INACTIVE`, `DISPOSED`, etc.)
  - `InventoryItem.item_type` (`FIXED_ASSET` / `CONSUMABLE`)
- Consumable stock state:
  - `ConsumableStock.quantity`, `min_threshold`, `reorder_alert_enabled`.
- Assignment state:
  - `ItemAssignment.status` (`ASSIGNED` / `RETURNED`) plus return metadata.
- Audit/history state:
  - `InventoryAuditLog` with before/after JSON snapshots and timestamps.

This is the core state model of the system.

## 2) Authentication State
Auth state is handled by JWT:
- Global DRF auth class: `rest_framework_simplejwt.authentication.JWTAuthentication`.
- Requests are authenticated by bearer token, not by server-side custom session store in app code.

Related note:
- Django `SessionMiddleware` is present in middleware stack (framework default), but this codebase’s API auth path is JWT-based.

## 3) Authorization/Access Scope State (Derived Per Request)
`common/access.py` computes effective data scope from user role + office hierarchy:
- Global roles -> unrestricted queryset scope.
- Scoped roles -> office-descendant filtered scope.
- Ward officer -> own office scope.

This is a derived runtime state, recomputed from persisted user/office data.

## 4) Policy State (Role Matrix)
`common/permissions.py` defines role-policy state in code constants:
- read-only role set,
- write role set,
- per-resource write matrix.

This policy state is static code-level configuration, not database-configurable in current files.

## 5) State Transitions Implemented
State transitions are explicit in domain flows:
- Stock transition:
  - transaction type + quantity changes `ConsumableStock.quantity`.
- Assignment transition:
  - `ASSIGNED -> RETURNED` with `returned_at` requirements.
- Inventory activity transition:
  - create/update/assign/return events recorded to audit log.

These transitions are enforced through serializers, model constraints, and view hooks.

## 6) Consistency Controls for State
Observed controls include:
- Model constraints (check/unique constraints in assignments).
- Serializer validation rules (item type vs category, stock quantity checks).
- Atomic DB transaction in consumable stock transaction serializer create.
- Indexed state fields for query performance (`status`, relation/time indexes).

## What Is Not Present
From scanned repository files:
- No frontend client-state store (Redux/Zustand/etc.) in this backend repo.
- No explicit distributed cache layer wiring in settings (for example configured `CACHES` backend).
- No event-sourcing framework; audit log is present but primary state remains relational model state.
- No workflow engine/state machine library usage detected.

## State Management Summary
State management is database-centric and request-driven:
- persistent domain state in models,
- access/auth state resolved per request,
- transitions validated in serializers/models,
- side-effect state captured in audit logs.

## Chapter 9 Outcome
You now understand exactly how state is stored, derived, protected, and transitioned in this backend, and which advanced state-management mechanisms are not implemented in current project code.
