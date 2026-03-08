# Context Log

This log is updated after each completed chapter.

## Chapter 1 � Project Overview
- Key Concepts Learned:
  - The repository is a Django REST backend for IMS with JWT auth and versioned APIs (`/api/` and `/api/v1/`).
  - Core business domains are split into dedicated apps: users, hierarchy, catalog, inventory, actions, audit, reports, and common.
  - Deployment/runtime path uses Gunicorn + WSGI with Render/Procfile support and a health endpoint.
- Files Covered:
  - `manage.py`
  - `django_project/settings.py`
  - `django_project/urls.py`
  - `requirements.txt`
  - `render.yaml`
  - `Procfile`
  - `gunicorn.conf.py`
  - App roots under `users/`, `hierarchy/`, `catalog/`, `inventory/`, `actions/`, `audit/`, `reports/`, `common/`
  - `PRD/PRD - IMS.md`, `PRD/BACKEND_PRD_ALIGNMENT.md`
- Architecture Insights:
  - DRF viewsets provide main CRUD APIs.
  - Permission and data-scope boundaries are centralized in `common` modules.
  - Legacy route support exists with explicit deprecation headers.
- Data Flow Insights:
  - Incoming API traffic routes through `django_project/urls.py` into per-app routers.
  - Authentication is JWT-based and enforced globally via DRF default auth/permission settings.
- Open Questions:
  - Celery/Redis packages are present in requirements, but task/worker configuration is not visible in scanned app files.
- Next Steps:
  - Proceed to Chapter 2 to formalize the architecture pattern and layer boundaries.

## Chapter 2 � Architecture Pattern
- Key Concepts Learned:
  - The project follows a modular monolith architecture with domain separation by Django app.
  - The request path is URL router -> DRF view/APIView -> serializer validation/business rules -> model/database.
  - Cross-cutting controls are centralized: role permissions, office-based queryset scoping, and legacy API deprecation headers.
- Files Covered:
  - `django_project/settings.py`
  - `django_project/urls.py`
  - `common/permissions.py`
  - `common/access.py`
  - `common/middleware.py`
  - Representative module files in `users/`, `inventory/`, `actions/`, `audit/`, `reports/`
- Architecture Insights:
  - Domain boundaries are clean at app level.
  - No separate service/repository layer is present in the current code.
  - API version transition is handled through dual route prefixes plus middleware signaling.
- Data Flow Insights:
  - Auth is globally enforced through DRF settings and JWT backend.
  - Data visibility is filtered per user role/office using shared scoping logic applied inside view querysets.
- Open Questions:
  - Async/background execution architecture is not implemented in visible code, despite related dependencies in requirements.
- Next Steps:
  - Proceed to Chapter 3 to map the complete folder and file structure in learning order.

## Chapter 3 � Folder Structure
- Key Concepts Learned:
  - The repository uses a conventional Django root + multi-app layout.
  - Domain concerns are split across dedicated app directories with repeating internal patterns.
  - Documentation and deployment concerns are separated into `PRD/`, `project_docs/`, and root config files.
- Files Covered:
  - Root folder listing
  - `django_project/`
  - `users/`, `hierarchy/`, `catalog/`, `inventory/`, `actions/`, `audit/`, `reports/`, `common/`
  - `PRD/`
  - `project_docs/`
- Architecture Insights:
  - Consistent app layout improves discoverability (`models`, `serializers`, `views`, `urls`, `tests`, `migrations`).
  - Management commands are intentionally placed under `catalog` and `common`.
  - Deployment/runtime files are centralized at the repository root.
- Data Flow Insights:
  - Folder layout mirrors flow boundaries: global config (`django_project`) -> domain APIs (apps) -> shared control (`common`) -> docs/reporting artifacts.
- Open Questions:
  - No additional infrastructure module directories (for example dedicated `services/` or `tasks/`) are visible in root/app layouts.
- Next Steps:
  - Proceed to Chapter 4 to map the exact technology stack from requirements and settings.

## Chapter 4 � Technology Stack
- Key Concepts Learned:
  - The runtime backbone is Python + Django + Django REST Framework.
  - JWT auth, filtering/search/ordering, throttling, and OpenAPI docs are explicitly configured in settings.
  - Reporting/export support is implemented using Excel and PDF libraries.
- Files Covered:
  - `requirements.txt`
  - `django_project/settings.py`
  - `render.yaml`
  - `Procfile`
  - `gunicorn.conf.py`
- Architecture Insights:
  - Deployment path is Gunicorn + WSGI with environment-driven settings.
  - Database strategy supports SQLite by default and PostgreSQL via `DATABASE_URL`.
  - Optional components (`whitenoise`, `corsheaders`) are conditionally enabled.
- Data Flow Insights:
  - Request auth/filter/pagination/throttle behavior is centralized through DRF global settings.
  - Output/report generation flows include CSV/Excel/PDF tooling in the backend stack.
- Open Questions:
  - Celery/Redis related packages are listed, but no explicit worker/task module wiring was found in current app code.
- Next Steps:
  - Proceed to Chapter 5 to build a dependency graph across apps and shared modules.

## Chapter 5 � Dependency Graph
- Key Concepts Learned:
  - App dependencies are explicit through cross-imports in models, serializers, views, and management commands.
  - `inventory` is the central domain dependency hub.
  - `common` acts as shared policy/scope infrastructure used by multiple domain apps.
- Files Covered:
  - `django_project/settings.py`
  - `django_project/urls.py`
  - `users/models.py`
  - `inventory/models.py`, `inventory/serializers.py`, `inventory/views.py`
  - `actions/models.py`, `actions/views.py`
  - `audit/models.py`, `audit/views.py`, `audit/utils.py`
  - `reports/views.py`
  - `common/access.py`, `common/permissions.py`, `common/management/commands/seed_prd_data.py`
- Architecture Insights:
  - `reports` depends on multiple domain apps for read-side aggregation.
  - `inventory` and `actions` have bidirectional coupling in current code.
  - Shared permission and scoping logic is intentionally centralized in `common`.
- Data Flow Insights:
  - Request routing fan-outs from project URLs into app routers.
  - Cross-module data joins and summaries are concentrated in report and action/inventory paths.
- Open Questions:
  - No dedicated service-interface abstraction exists to decouple cross-app dependencies.
- Next Steps:
  - Proceed to Chapter 6 for entry-point analysis from process start to URL dispatch.

## Chapter 6 � Entry Point Analysis
- Key Concepts Learned:
  - The backend has three entrypoint forms: CLI (`manage.py`), WSGI (`wsgi.py`), and ASGI (`asgi.py`).
  - Production startup in repository configs uses WSGI + Gunicorn.
  - URL dispatch starts from `ROOT_URLCONF` after middleware execution.
- Files Covered:
  - `manage.py`
  - `django_project/wsgi.py`
  - `django_project/asgi.py`
  - `django_project/settings.py`
  - `django_project/urls.py`
  - `Procfile`
  - `render.yaml`
  - `gunicorn.conf.py`
- Architecture Insights:
  - Deployment commands chain migrations/static/bootstrap before server launch.
  - Gunicorn config file is a core runtime entry dependency.
  - ASGI entrypoint exists but is not the configured production process path in current deployment files.
- Data Flow Insights:
  - First request path is: server process -> WSGI app -> middleware -> root URL router -> app route/view.
  - Health checks and auth token endpoints are explicit public entry routes.
- Open Questions:
  - No separate worker/process entry commands are configured for background task execution.
- Next Steps:
  - Proceed to Chapter 7 for end-to-end request lifecycle analysis through view, serializer, model, and response.

## Chapter 7 � Request Lifecycle
- Key Concepts Learned:
  - Request lifecycle is layered: route -> middleware -> auth/permission -> view action -> serializer/model -> response.
  - Write flows include post-save side effects such as audit log creation.
  - Read flows apply office-based queryset scoping before response serialization.
- Files Covered:
  - `django_project/urls.py`
  - `common/middleware.py`
  - `common/permissions.py`
  - `common/access.py`
  - `inventory/views.py`
  - `inventory/serializers.py`
  - `inventory/models.py`
  - `audit/utils.py`
- Architecture Insights:
  - Permission and scope checks are centralized and reused across viewsets.
  - Serializer layer contains significant business validation and transactional mutation logic.
  - View `perform_create/perform_update` hooks are used for cross-cutting audit behavior.
- Data Flow Insights:
  - Input payloads pass serializer validation before persistence.
  - Stock transaction flow mutates quantity atomically and computes balance snapshots.
  - Legacy API paths append deprecation metadata on outgoing responses.
- Open Questions:
  - No explicit global exception mapping layer beyond DRF defaults is visible in scanned files.
- Next Steps:
  - Proceed to Chapter 8 to map full data pipelines (create/update/report/export and seed flows).

## Chapter 8 � Data Pipeline
- Key Concepts Learned:
  - Data moves through multiple pipeline types: CRUD, bulk import, stock transactions, assignments, reports, and seed commands.
  - Validation and transformation are concentrated in serializers; side effects are triggered in view hooks.
  - Reporting/export pipeline converts scoped querysets into JSON/CSV/Excel/PDF outputs.
- Files Covered:
  - `inventory/views.py`
  - `inventory/serializers.py`
  - `actions/views.py`
  - `audit/utils.py`
  - `reports/views.py`
  - `common/access.py`
  - `common/management/commands/seed_prd_data.py`
  - `catalog/management/commands/seed_initial_categories.py`
- Architecture Insights:
  - Pipeline orchestration is mostly view-driven with serializer-level transactional logic where needed.
  - Audit logging is a shared downstream pipeline for multiple domain writes.
  - Seed commands implement a separate deterministic initialization pipeline.
- Data Flow Insights:
  - CSV file inputs are row-normalized into serializer payloads with partial-failure summaries.
  - Stock transaction pipeline updates balances atomically and can emit notification side effects.
  - Report pipelines reuse scoped querysets and branch into API JSON or file export outputs.
- Open Questions:
  - No asynchronous or queue-backed processing path is present in visible app code for heavy pipelines.
- Next Steps:
  - Proceed to Chapter 9 to assess state management patterns that exist in this backend.

## Chapter 9 � State Management (if exists)
- Key Concepts Learned:
  - State is primarily database-backed (users, inventory, stock, assignments, audit logs).
  - Auth state is JWT-based and request-driven.
  - Access scope state is derived per request from role + office hierarchy.
- Files Covered:
  - `django_project/settings.py`
  - `users/models.py`
  - `inventory/models.py`
  - `actions/models.py`
  - `audit/models.py`
  - `common/access.py`
  - `common/permissions.py`
- Architecture Insights:
  - Policy state (role matrix) is static code configuration.
  - State transitions are implemented across serializer/model/view layers with constraints and atomic blocks.
  - Audit records provide historical state snapshots alongside primary current-state tables.
- Data Flow Insights:
  - Write flows mutate persistent state and emit audit state.
  - Read flows depend on derived visibility state from scoping logic.
  - Stock and assignment states have explicit transition rules and validation gates.
- Open Questions:
  - No explicit cache backend configuration or advanced state machine/workflow framework is visible in current code.
- Next Steps:
  - Proceed to Chapter 10 to document external integrations and interface boundaries.

## Chapter 10 � External Integrations
- Key Concepts Learned:
  - External integrations in this backend are primarily auth/docs/email/db/deployment/origin interfaces.
  - Most integration behavior is controlled through environment-driven settings.
  - Some dependency ecosystems exist in `requirements.txt` without visible runtime wiring in app code.
- Files Covered:
  - `django_project/settings.py`
  - `django_project/urls.py`
  - `inventory/views.py`
  - `reports/views.py`
  - `render.yaml`
  - `Procfile`
  - `requirements.txt`
- Architecture Insights:
  - JWT, schema docs, and deployment platform hooks are first-class integrations.
  - Email integration is event-triggered from stock transaction flow.
  - Frontend/proxy integration points are explicit via CORS/CSRF/proxy settings.
- Data Flow Insights:
  - Token endpoints and docs endpoints provide external API entry contracts.
  - Low-stock events can flow to outbound email recipients.
  - Report data can be exported into externally consumable file formats (CSV/Excel/PDF).
- Open Questions:
  - Celery/Redis integration path is dependency-present but not implemented in visible runtime/deployment modules.
- Next Steps:
  - Proceed to Chapter 11 for detailed runtime and deployment file breakdown.

## Chapter 11 � Core Runtime & Deployment Files
- Key Concepts Learned:
  - Runtime/deployment responsibilities are concentrated in a small set of root and project config files.
  - Startup flow is command-driven: management tasks first, then Gunicorn serving WSGI app.
  - Render and Procfile provide two explicit deployment contracts in this repository.
- Files Covered:
  - `manage.py`
  - `django_project/settings.py`
  - `django_project/urls.py`
  - `django_project/asgi.py`
  - `django_project/wsgi.py`
  - `gunicorn.conf.py`
  - `Procfile`
  - `render.yaml`
  - `.smoke_test.py`
- Architecture Insights:
  - `settings.py` is the central runtime contract controlling app, middleware, auth, DB, and security behavior.
  - Deployment path currently targets WSGI rather than ASGI.
  - Gunicorn tuning is externalized in dedicated config for operational control.
- Data Flow Insights:
  - Deployment chain feeds directly into request dispatch chain (`wsgi` -> settings -> urls -> app endpoints).
  - Smoke test script validates several end-to-end API flows after runtime startup.
- Open Questions:
  - No separate worker process startup contract is defined in deployment manifests.
- Next Steps:
  - Proceed to Chapter 12 for full users app file breakdown.

## Chapter 12 � Users App Files
- Key Concepts Learned:
  - The project uses a custom `AbstractUser` extension with role and office linkage.
  - User API has bootstrap-first creation logic (open only when no users exist).
  - Self-service updates are protected against privilege escalation at serializer level.
- Files Covered:
  - `users/models.py`
  - `users/serializers.py`
  - `users/views.py`
  - `users/urls.py`
  - `users/tests.py`
  - `users/admin.py`
  - `users/apps.py`
  - `users/migrations/0001_initial.py`
  - `users/migrations/0002_alter_user_role.py`
  - `users/migrations/0003_user_office.py`
- Architecture Insights:
  - Permission logic combines action-level policies, object-level checks, and queryset scoping.
  - User role model is foundational for permission and data-scope systems in other apps.
  - Migration history shows role expansion and later office linkage evolution.
- Data Flow Insights:
  - Password flow enforces confirmation and uses secure hash storage.
  - Non-staff user queries are constrained to self record.
  - Admin paths retain full user lifecycle control.
- Open Questions:
  - No dedicated password policy beyond Django validators configured globally is defined inside users app files.
- Next Steps:
  - Proceed to Chapter 13 for hierarchy app file analysis and its role in office tree scoping.

## Chapter 13 � Hierarchy App Files
- Key Concepts Learned:
  - Hierarchy app models office structure as a self-referential tree.
  - Office API is protected by role matrix and queryset scoping logic.
  - Hierarchy data is foundational for user office linkage and cross-app visibility controls.
- Files Covered:
  - `hierarchy/models.py`
  - `hierarchy/serializers.py`
  - `hierarchy/views.py`
  - `hierarchy/urls.py`
  - `hierarchy/tests.py`
  - `hierarchy/admin.py`
  - `hierarchy/apps.py`
  - `hierarchy/migrations/0001_initial.py`
  - `hierarchy/migrations/0002_alter_office_level.py`
- Architecture Insights:
  - Self-FK with `PROTECT` preserves parent-child office relationships.
  - Access control is delegated to shared `common` permission/scope modules.
  - Migration history reflects correction of office level choice values.
- Data Flow Insights:
  - Office CRUD requests flow through scoped queryset filtering by accessible office IDs.
  - Location code uniqueness supports stable office identification in APIs and seeds.
- Open Questions:
  - No dedicated cycle-prevention validation for parent-office assignment is visible in serializer/model code.
- Next Steps:
  - Proceed to Chapter 14 for catalog app analysis (categories + custom field definitions).

## Chapter 14 � Catalog App Files
- Key Concepts Learned:
  - Catalog app defines category taxonomy and per-category dynamic custom field schema.
  - Catalog APIs are full CRUD with role-based write restrictions via shared permission policy.
  - Seed command provides idempotent baseline category initialization.
- Files Covered:
  - `catalog/models.py`
  - `catalog/serializers.py`
  - `catalog/views.py`
  - `catalog/urls.py`
  - `catalog/tests.py`
  - `catalog/admin.py`
  - `catalog/apps.py`
  - `catalog/migrations/0001_initial.py`
  - `catalog/migrations/0002_customfielddefinition_is_unique_and_more.py`
  - `catalog/management/commands/seed_initial_categories.py`
- Architecture Insights:
  - Catalog is upstream of inventory validation and item-type compatibility rules.
  - Dynamic field definitions allow extensible metadata without changing inventory model columns.
  - Constraint/index design enforces uniqueness and query efficiency for custom fields.
- Data Flow Insights:
  - Category and custom-field CRUD requests pass through standard DRF viewset filter/search/ordering flow.
  - Seed pipeline updates category consumable flags to maintain consistency with PRD defaults.
- Open Questions:
  - No custom validation logic exists for `select_options` consistency with `field_type=SELECT` in serializer/model files.
- Next Steps:
  - Proceed to Chapter 15 for full inventory app file analysis.

## Chapter 15 � Inventory App Files
- Key Concepts Learned:
  - Inventory app is the core domain module for items, fixed assets, consumable stocks, and stock transactions.
  - Validation and consistency controls exist across model `clean`, serializer checks, and atomic transaction logic.
  - Inventory write paths trigger cross-cutting side effects (audit logs and low-stock email alerts).
- Files Covered:
  - `inventory/models.py`
  - `inventory/serializers.py`
  - `inventory/views.py`
  - `inventory/urls.py`
  - `inventory/tests.py`
  - `inventory/admin.py`
  - `inventory/apps.py`
  - `inventory/migrations/0001_initial.py`
  - `inventory/migrations/0002_consumablestock_initial_quantity_and_more.py`
  - `inventory/migrations/0003_consumablestocktransaction_inventoryitem_amount_and_more.py`
- Architecture Insights:
  - Inventory acts as a central dependency for actions, audit, and reports.
  - Subtype modeling via one-to-one tables enforces fixed-asset vs consumable separation.
  - Migration history shows progressive expansion from core records to full operational tracking.
- Data Flow Insights:
  - CRUD and bulk-import pipelines pass through scoped viewsets and serializer validation.
  - Stock transaction pipeline updates quantities atomically and stores resulting balances.
  - Computed response fields expose assignment/serial/stock status derived from related tables.
- Open Questions:
  - No explicit idempotency-key mechanism is visible for repeated stock transaction submission handling.
- Next Steps:
  - Proceed to Chapter 16 for actions app analysis (assignment workflow layer).

## Chapter 16 � Actions App Files
- Key Concepts Learned:
  - Actions app implements assignment/return workflow over inventory items.
  - Data integrity is protected by target-required and one-active-assignment constraints.
  - Assignment operations emit audit events with before/after context.
- Files Covered:
  - `actions/models.py`
  - `actions/serializers.py`
  - `actions/views.py`
  - `actions/urls.py`
  - `actions/tests.py`
  - `actions/admin.py`
  - `actions/apps.py`
  - `actions/migrations/0001_initial.py`
  - `actions/migrations/0002_itemassignment_assign_till.py`
- Architecture Insights:
  - Actions sits between inventory ownership state and audit trail state.
  - Office-based queryset scoping is applied through shared access helper.
  - Custom action endpoints provide assignment analytics and bulk ingestion paths.
- Data Flow Insights:
  - Create/update assignment flows include automatic assignment actor attribution and audit writes.
  - Bulk CSV import pipeline validates row-by-row and returns aggregated success/failure summary.
  - Summary-by-assignee endpoint transforms assignment records into grouped operational metrics.
- Open Questions:
  - No explicit automatic expiry or scheduler-driven transition when `assign_till` passes is visible in app code.
- Next Steps:
  - Proceed to Chapter 17 for audit app analysis.

## Chapter 17 � Audit App Files
- Key Concepts Learned:
  - Audit events are stored in `InventoryAuditLog` with structured before/after JSON.
  - Audit API is intentionally read-only through `ReadOnlyModelViewSet`.
- Files Covered:
  - `audit/models.py`, `audit/serializers.py`, `audit/views.py`, `audit/urls.py`, `audit/utils.py`, `audit/tests.py`
- Architecture Insights:
  - Audit write path is explicit (utility calls from business viewsets), not signal-based.
- Data Flow Insights:
  - Inventory/actions write operations call `create_inventory_audit_log`, then reports/audit endpoints read scoped logs.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Proceed to report endpoint analysis.

## Chapter 18 � Reports App Files
- Key Concepts Learned:
  - Reports are APIViews with scoped querysets and aggregate annotations.
  - CSV/Excel/PDF exports reuse inventory report filtering.
- Files Covered:
  - `reports/views.py`, `reports/urls.py`, `reports/tests.py`, `reports/models.py`
- Architecture Insights:
  - Reporting logic is centralized in `reports/views.py`; no report-specific models yet.
- Data Flow Insights:
  - Queryset filtering -> serialization/export rendering -> HTTP response.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Analyze shared access and permission layer.

## Chapter 19 � Common App Files
- Key Concepts Learned:
  - `IMSAccessPermission` enforces role-based write matrix.
  - Office hierarchy scoping is centralized in `common/access.py`.
  - Middleware adds deprecation headers for legacy `/api/*` routes.
- Files Covered:
  - `common/access.py`, `common/permissions.py`, `common/middleware.py`, command files, tests, app placeholders.
- Architecture Insights:
  - Cross-cutting behavior is isolated in `common` and reused by all major apps.
- Data Flow Insights:
  - Permission and scope checks are applied before domain querysets are returned.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Review schema evolution across migration history.

## Chapter 20 � Migrations Across Apps
- Key Concepts Learned:
  - App schemas evolved in staged migrations: initial tables first, then role/field/workflow expansion.
- Files Covered:
  - Migration files across `users`, `hierarchy`, `catalog`, `inventory`, `actions`, `audit`.
- Architecture Insights:
  - Cross-app dependencies are explicit and orderly in migration dependencies.
- Data Flow Insights:
  - Later migrations support richer runtime flows (transactions, assignments, audit).
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Cross-check implementation with requirement documents.

## Chapter 21 � Requirements and Product Reference Files
- Key Concepts Learned:
  - PRD defines expected modules; alignment doc tracks completed vs pending backend features.
  - `requirements.txt` includes async packages, but task module implementation is not present.
- Files Covered:
  - `requirements.txt`, `PRD/PRD - IMS.md`, `PRD/BACKEND_PRD_ALIGNMENT.md`, `PRD/PRD - IMS.pdf`, `data.json`
- Architecture Insights:
  - Current codebase aligns with core PRD modules (inventory, assignment, audit, reports, RBAC).
- Data Flow Insights:
  - `data.json` reflects seeded relational data shape used by the domain model.
- Open Questions:
  - Async job architecture remains unimplemented in visible source.
- Next Steps:
  - Start line-by-line deep dives.

## Chapter 22 � Deep Dive: `django_project/settings.py`
- Key Concepts Learned:
  - Settings are environment-driven with helper functions and production guardrails.
- Files Covered:
  - `django_project/settings.py`
- Architecture Insights:
  - Conditional middleware/app insertion supports optional dependencies (`corsheaders`, `whitenoise`).
- Data Flow Insights:
  - Global DRF auth/permission/filter/throttle config affects all API endpoints.
- Open Questions:
  - No Celery config found in settings.
- Next Steps:
  - Deep-dive root URL composition.

## Chapter 23 � Deep Dive: `django_project/urls.py`
- Key Concepts Learned:
  - Root URLs expose dual route families (`/api/*` and `/api/v1/*`) for all app routes.
- Files Covered:
  - `django_project/urls.py`
- Architecture Insights:
  - Version transition is additive; no route removal yet.
- Data Flow Insights:
  - Request enters project router before app-level routers/paths.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Deep-dive permission + access control internals.

## Chapter 24 � Deep Dive: `common/permissions.py` and `common/access.py`
- Key Concepts Learned:
  - Write authorization and data visibility are separate but coordinated layers.
- Files Covered:
  - `common/permissions.py`, `common/access.py`
- Architecture Insights:
  - Per-resource role matrix provides fine-grained control without app-specific permission classes.
- Data Flow Insights:
  - Office subtree traversal controls queryset bounds for scoped roles.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Deep-dive users module.

## Chapter 25 � Deep Dive: `users/models.py`, `users/serializers.py`, `users/views.py`
- Key Concepts Learned:
  - User management protects privileged self-update fields.
  - First-user bootstrap path allows creation only when user table is empty.
- Files Covered:
  - `users/models.py`, `users/serializers.py`, `users/views.py`
- Architecture Insights:
  - Object-level access policy (`IsSelfOrAdmin`) keeps non-staff visibility to self.
- Data Flow Insights:
  - Password handling is serializer-managed with confirmation validation.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Deep-dive hierarchy module.

## Chapter 26 � Deep Dive: `hierarchy/models.py`, `hierarchy/views.py`
- Key Concepts Learned:
  - Hierarchy model is tree-based and underpins office data scoping logic.
- Files Covered:
  - `hierarchy/models.py`, `hierarchy/views.py`
- Architecture Insights:
  - Parent-child office structure is central to access boundaries.
- Data Flow Insights:
  - View querysets are scoped using office IDs from shared access helper.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Deep-dive catalog metadata module.

## Chapter 27 � Deep Dive: `catalog/models.py`, `catalog/views.py`, `catalog/serializers.py`
- Key Concepts Learned:
  - Catalog supports dynamic field metadata per category with uniqueness constraint.
- Files Covered:
  - `catalog/models.py`, `catalog/serializers.py`, `catalog/views.py`
- Architecture Insights:
  - Dynamic custom fields avoid hardcoding item-specific columns.
- Data Flow Insights:
  - Catalog metadata influences inventory validation and UI form structure.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Deep-dive inventory domain model.

## Chapter 28 � Deep Dive: `inventory/models.py`
- Key Concepts Learned:
  - Inventory separates shared item core from fixed-asset and consumable subtype tables.
- Files Covered:
  - `inventory/models.py`
- Architecture Insights:
  - Model `clean()` enforces subtype/category consistency.
- Data Flow Insights:
  - Consumable transactions track movement history and resulting stock balances.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Deep-dive serializer mutation logic.

## Chapter 29 � Deep Dive: `inventory/serializers.py`
- Key Concepts Learned:
  - Serializer layer enforces category/type/subtype rules and transactional stock updates.
- Files Covered:
  - `inventory/serializers.py`
- Architecture Insights:
  - Business safeguards are enforced before view hooks are reached.
- Data Flow Insights:
  - Stock transaction serializer mutates `ConsumableStock.quantity` and stores `balance_after` atomically.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Deep-dive inventory viewset hooks.

## Chapter 30 � Deep Dive: `inventory/views.py`
- Key Concepts Learned:
  - Inventory viewsets add audit hooks, CSV bulk import, and low-stock email side effects.
- Files Covered:
  - `inventory/views.py`
- Architecture Insights:
  - View layer currently carries non-trivial orchestration logic.
- Data Flow Insights:
  - Request write -> serializer save -> audit write -> optional notification.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Deep-dive assignment workflow module.

## Chapter 31 � Deep Dive: `actions/models.py`, `actions/serializers.py`, `actions/views.py`
- Key Concepts Learned:
  - Assignment workflow is protected by DB constraints + serializer validation + view audit hooks.
- Files Covered:
  - `actions/models.py`, `actions/serializers.py`, `actions/views.py`
- Architecture Insights:
  - Conditional unique constraint prevents duplicate active assignments for one item.
- Data Flow Insights:
  - Assignment updates emit `ASSIGN` or `RETURN` audit actions.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Deep-dive audit internals.

## Chapter 32 � Deep Dive: `audit/models.py`, `audit/views.py`, `audit/utils.py`
- Key Concepts Learned:
  - Audit is a shared event ledger consumed by reports and direct audit APIs.
- Files Covered:
  - `audit/models.py`, `audit/views.py`, `audit/utils.py`
- Architecture Insights:
  - Helper-driven writes keep audit payload format consistent.
- Data Flow Insights:
  - Domain writes in inventory/actions feed the audit stream.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Deep-dive reporting internals.

## Chapter 33 � Deep Dive: `reports/views.py`
- Key Concepts Learned:
  - Reporting endpoints use scoped querysets and aggregations with export format adapters.
- Files Covered:
  - `reports/views.py`
- Architecture Insights:
  - One filter core (`get_queryset`) is reused by JSON/CSV/Excel/PDF report paths.
- Data Flow Insights:
  - Filtered inventory query drives all output formats.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Deep-dive management commands.

## Chapter 34 � Deep Dive: Seed and bootstrap commands
- Key Concepts Learned:
  - Command layer provides idempotent environment bootstrap and sample dataset creation.
- Files Covered:
  - `common/management/commands/bootstrap_admin.py`, `common/management/commands/seed_prd_data.py`, `catalog/management/commands/seed_initial_categories.py`
- Architecture Insights:
  - Commands are deterministic and dry-run aware.
- Data Flow Insights:
  - Seed pipeline creates interdependent records in correct order.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Review test strategy and coverage.

## Chapter 35 � Deep Dive: Test Suite and `.smoke_test.py`
- Key Concepts Learned:
  - Test suite focuses on RBAC, scope behavior, exports, and audit hooks.
- Files Covered:
  - All `*/tests.py` files and `.smoke_test.py`
- Architecture Insights:
  - Tests are behavior-focused around API contracts rather than internal implementation details.
- Data Flow Insights:
  - Smoke script validates end-to-end flow from token generation to inventory/actions/audit/report endpoints.
- Open Questions:
  - Command and some edge-case branches remain under-tested.
- Next Steps:
  - Start rebuild/refactor planning chapters.

## Chapter 36 � Guided Rebuild
- Key Concepts Learned:
  - Rebuild should follow dependency order: users/hierarchy/catalog -> inventory -> actions/audit/reports -> common commands/tests.
- Files Covered:
  - Synthesis chapter based on prior references.
- Architecture Insights:
  - Layering order reduces migration and dependency conflicts.
- Data Flow Insights:
  - Core auth/scope/audit contracts should be verified at each rebuild stage.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Capture concrete architecture improvements.

## Chapter 37 � Architecture Improvements
- Key Concepts Learned:
  - Main opportunity is extracting repeated business orchestration from viewsets into reusable service modules.
- Files Covered:
  - Synthesis chapter based on observed code duplication.
- Architecture Insights:
  - Separation of orchestration from transport layer improves maintainability/testability.
- Data Flow Insights:
  - Existing flows remain valid; proposed improvements restructure implementation boundaries.
- Open Questions:
  - Service/task layer not present in current repo.
- Next Steps:
  - Convert improvements into refactor-safe execution plan.

## Chapter 38 � Refactoring
- Key Concepts Learned:
  - Refactoring should prioritize duplicated patterns (scope hooks, CSV loops, audit payload builders).
- Files Covered:
  - Synthesis chapter grounded in observed modules.
- Architecture Insights:
  - Test-first incremental refactors minimize regression risk.
- Data Flow Insights:
  - Endpoint contracts should remain stable while internals are simplified.
- Open Questions:
  - None in this chapter.
- Next Steps:
  - Evaluate performance posture and optimization priorities.

## Chapter 39 � Performance Review
- Key Concepts Learned:
  - Current code has useful indexes/select_related/pagination/throttling, with predictable high-load pressure points.
- Files Covered:
  - Synthesis chapter based on models/views/settings.
- Architecture Insights:
  - Report/export and import paths are top candidates for scaling improvements.
- Data Flow Insights:
  - Heavy list-building and synchronous side effects can increase request latency.
- Open Questions:
  - Async execution model is still missing in reference implementation.
- Next Steps:
  - Course complete.

## Chapter 40 — Backend Operations and Hardening Update
- Key Concepts Learned:
  - Backend now includes scheduled backup, restore drill, and SLO monitor operations.
  - Notification flows now support provider-aware delivery tracking and webhook-driven status updates.
  - CI now enforces lifecycle and security posture gates plus backup/restore validation.
- Files Covered:
  - common/notifications.py
  - common/tasks.py
  - common/backups.py
  - common/observability.py
  - common/management/commands/run_backup.py
  - common/management/commands/run_restore_drill.py
  - .github/workflows/ci.yml
  - .github/workflows/security.yml
  - scripts/check_endpoint_lifecycle.py
  - scripts/check_security_posture.py
  - PRD/BACKEND_OPERATIONS_RUNBOOK.md
- Architecture Insights:
  - Operational maturity moved from “planned” to implemented code with DB-tracked run history.
- Data Flow Insights:
  - Scheduler and command flows now produce auditable operational records and threshold-based alerts.
- Open Questions:
  - SIEM/APM platform integration and government hardening sign-off remain environment execution tasks.
- Next Steps:
  - Validate end-to-end behavior in staging and then execute production readiness checklist with DevOps/Security.