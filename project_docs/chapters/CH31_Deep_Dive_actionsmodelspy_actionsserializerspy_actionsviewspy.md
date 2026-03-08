# Chapter 31 — Deep Dive: `actions/models.py`, `actions/serializers.py`, `actions/views.py`

## Learning Goals
- Understand assignment lifecycle rules and API hooks.

## Reference Files
- `actions/models.py`
- `actions/serializers.py`
- `actions/views.py`

## Deep Dive Walkthrough

## 1) Model constraints
- `ItemAssignment` requires at least one target (`assigned_to_user` or `assigned_to_office`).
- Enforces one active assignment per item using conditional unique constraint on `status=ASSIGNED`.
- Requires `returned_at` when status is `RETURNED`.

## 2) Serializer checks
- `ItemAssignmentSerializer.validate` mirrors model business rules.
- Exposes `item_name` and `item_number` read-only fields.

## 3) Viewset lifecycle
- Queryset is office-scoped and permission-protected.
- `perform_create` sets `assigned_by` and writes `ASSIGN` audit log.
- `perform_update` compares before/after state and writes `ASSIGN` or `RETURN` audit event.

## 4) Custom actions
- `summary_by_assignee`: grouped totals with `active`, `overdue`, `returned` metrics.
- `bulk_import`: CSV-driven assignment creation with per-row validation + audit logs.

## Chapter 31 Outcome
You can now explain assignment workflow integrity from database constraints to API-level audit side effects.
