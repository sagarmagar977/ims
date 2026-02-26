# IMS Backend PRD Alignment (Status)

## Completed
- JWT authentication endpoints for login/refresh.
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
- Role-based read/write access baseline (Finance/Audit read-only).
- Hierarchy-based office scoping for data visibility (central/provincial/local/ward).

## Partially Completed
- Hierarchical RBAC: office scope implemented, but no fine-grained policy matrix per endpoint/action beyond current role model.

## Not Completed Yet (Backend)
- Background job/scheduler for periodic alerts and report generation.
- Integration with real email/SMS providers and delivery tracking.
- Comprehensive test suite across all apps (currently baseline tests only).
- API versioning strategy and deprecation policy.
- Full production hardening (rate limiting, security headers tuning, backup orchestration, observability dashboards).

## Operational Note
- Default SQLite path is now auto-fallback to writable locations (usually `%TEMP%\\ims\\db.sqlite3`) to avoid prior workspace drive I/O errors.
