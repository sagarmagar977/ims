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
- Celery scheduler/worker integration for periodic low-stock alerts and report generation.
- Real provider integration paths for notifications:
  - Email via Django backend or SendGrid API.
  - SMS via Twilio API.
  - Delivery tracking persisted in `common.NotificationDelivery`.
- Endpoint lifecycle/deprecation calendar documented and enforced by CI gate script + workflow.
- Backup orchestration implemented:
  - Scheduled backup task + manual backup command.
  - Restore drill task + manual restore drill command.
  - Backup and restore drill execution history tracked in DB.
- Observability and SLO instrumentation implemented:
  - Operational status and SLO endpoints.
  - Periodic SLO monitor with alert notifications.
  - Runbook documenting jobs, thresholds, and operations.
- Security hardening checks implemented:
  - Security posture gate script in CI.
  - Automated dependency audit (`pip-audit`) and static analysis (`bandit`) workflow.

## Partially Completed
- Comprehensive test suite across all apps is improved from baseline, but still not exhaustive for all business flows and edge cases.
- Full production hardening is in progress:
  - Completed in this pass: DRF throttling baseline, lifecycle/deprecation governance, backup/restore drill automation, and security CI gates.
  - Remaining: external SIEM/APM integrations and production dashboard wiring in target infra.

## Not Completed Yet (Backend)
- External SIEM/APM platform integration (e.g., cloud-native dashboards and long-term log retention backend).
- Government production environment hardening validation sign-off checklist execution.

## Operational Note
- Default SQLite path is now auto-fallback to writable locations (usually `%TEMP%\\ims\\db.sqlite3`) to avoid prior workspace drive I/O errors.
