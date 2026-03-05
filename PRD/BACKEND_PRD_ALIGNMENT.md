# IMS Backend PRD Alignment (Status)

## Completed
- JWT authentication endpoints for login/refresh.
- API versioning routes added (`/api/v1/*`) while preserving existing `/api/*`.
- Legacy API deprecation headers on `/api/*` responses (`Deprecation`, `Sunset`, `Link`).
- Category management and dynamic custom field definitions.
- Inventory item CRUD with fixed-asset vs consumable typing.
- Bulk CSV import for inventory items.
- Consumable stock management with threshold logic.
- Consumable stock transactions with running balance updates.
- Low-stock alert trigger (email backend configurable).
- Assignment workflow with due date (`assign_till`) and return support.
- Prevent double-assignment for active assignments.
- Assignment bulk CSV import and assignee summary API.
- Audit log model + automatic audit log creation on core actions.
- Dashboard summary and recent activity APIs for UI cards/tables.
- Filterable inventory report API.
- Inventory CSV export endpoint.
- Inventory Excel export endpoint.
- Inventory PDF export endpoint.
- Fine-grained RBAC policy matrix per endpoint/action:
  - `offices`, `categories`, `custom-fields`: Central-only write roles.
  - `inventory-items`, `fixed-assets`, `consumable-stocks`: operational admin write roles.
  - `item-assignments`: operational admin write roles (ward write blocked).
  - `consumable-stock-transactions`: operational admin + ward write.
  - `audit-logs`: read-only API.
- Hierarchy-based office scoping for data visibility (central/provincial/local/ward).
- DRF rate limiting baseline configured (anon/user throttle classes + env-configurable rates).
- Design-to-backend screen alignment reviewed for:
  - Dashboard, Items, Categories, Assignments, Consumable Stock, Audit Log, and Filter modal.
- Test coverage expanded for RBAC + routing behavior across `common`, `catalog`, `hierarchy`, `actions`, `audit`, `inventory`, and `reports`.

## Partially Completed
- Comprehensive test suite across all apps is improved from baseline, but still not exhaustive for all business flows and edge cases.
- Full production hardening is in progress:
  - Completed in this pass: DRF throttling baseline and legacy API deprecation signaling.
  - Remaining: backup orchestration, observability dashboards, and deeper security hardening checks.

## Not Completed Yet (Backend)
- Background job/scheduler for periodic alerts and report generation.
- Integration with real email/SMS providers and delivery tracking.
- Fully documented endpoint lifecycle/deprecation calendar and automated enforcement gates in CI.

## Operational Note
- Default SQLite path is now auto-fallback to writable locations (usually `%TEMP%\\ims\\db.sqlite3`) to avoid prior workspace drive I/O errors.
