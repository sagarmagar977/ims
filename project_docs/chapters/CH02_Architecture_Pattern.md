# Chapter 2 Architecture Pattern

## Learning Goals
- Identify the architecture pattern implemented in this repository.
- Understand how responsibilities are split across Django apps.
- Distinguish global cross-cutting concerns from domain modules.

## Reference Files
- `django_project/settings.py`
- `django_project/urls.py`
- `common/permissions.py`
- `common/access.py`
- `common/middleware.py`
- `users/views.py`, `users/serializers.py`, `users/models.py`
- `inventory/views.py`, `inventory/serializers.py`, `inventory/models.py`
- `actions/views.py`, `audit/views.py`, `reports/views.py`

## Architecture Pattern Identified
The project uses a **modular monolith** architecture with **Django app-level domain segmentation**.

- Modular monolith:
  - One deployable backend service.
  - Multiple domain modules inside the same codebase and database.

- App-level segmentation:
  - `users` for identity/roles
  - `hierarchy` for office tree
  - `catalog` for category and custom fields
  - `inventory` for items/assets/consumable stock/stock transactions
  - `actions` for assignment workflows
  - `audit` for audit trail
  - `reports` for read/report/export endpoints
  - `common` for shared access, permission, and middleware concerns

## Request Handling Layering (Observed)
1. URL routing layer:
   - Root URL config includes each app router under `/api/` and `/api/v1/`.
2. View layer (DRF ViewSet/APIView):
   - Handles endpoints, filtering, ordering, permission checks, and custom actions.
3. Serializer layer:
   - Performs validation and data transformation.
   - In some cases performs transactional business logic (for example stock balance mutation in `ConsumableStockTransactionSerializer.create`).
4. Model layer:
   - Defines persistence schema, constraints, and entity-level integrity rules (`clean`, unique constraints, check constraints).
5. Database:
   - Default SQLite configuration; PostgreSQL supported via `DATABASE_URL`.

## Cross-Cutting Architecture Components
- Authentication and authorization:
  - Global DRF defaults enforce JWT authentication and authenticated access.
  - `IMSAccessPermission` applies role-based write/read policy.

- Data scope control:
  - `scope_queryset_by_user` filters querysets by office visibility rules (global vs scoped roles).

- API version transition strategy:
  - Middleware adds deprecation headers on legacy `/api/*` paths while `/api/v1/*` remains active.

## Architecture Characteristics
- Strengths observed:
  - Clear domain boundaries by Django app.
  - Consistent DRF patterns across modules.
  - Centralized permission and access-scope logic.
  - Built-in API version migration signaling.

- Tradeoffs observed:
  - No separate service/repository layer is present; some business logic lives in serializers/views.
  - Some dependencies in `requirements.txt` are not represented by visible runtime modules (for example Celery task modules are not present in scanned files).

## What Is Not Present (From Current Files)
- No microservice split.
- No separate frontend project in this repository.
- No dedicated event bus or message-driven workflow implementation in visible app code.

## Chapter 2 Outcome
You now have a concrete pattern map: this is a modular monolith Django REST system, organized by domain apps, with shared permission/scope middleware patterns and view-serializer-model request layering.
