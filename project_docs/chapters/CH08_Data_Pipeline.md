# Chapter 8 — Data Pipeline

## Learning Goals
- Understand how data enters, transforms, persists, and exits this system.
- Identify write pipelines, read/report pipelines, and initialization pipelines.
- Map where validation, scoping, audit logging, and export formatting occur.

## Reference Files
- `inventory/views.py`
- `inventory/serializers.py`
- `actions/views.py`
- `audit/utils.py`
- `reports/views.py`
- `common/access.py`
- `common/management/commands/seed_prd_data.py`
- `catalog/management/commands/seed_initial_categories.py`

## Pipeline Categories in This Project
1. Transactional API write pipelines (create/update/bulk import)
2. Transactional stock mutation pipeline
3. Assignment pipeline
4. Audit trail pipeline
5. Read aggregation/report/export pipeline
6. Bootstrap/seed data pipeline

## 1) Inventory Item Create/Update Pipeline
```text
HTTP request
-> inventory viewset action
-> serializer validation (category/item_type rules)
-> model save
-> audit log write (CREATE/UPDATE + snapshot)
-> response payload
```

Observed implementation:
- Input source: JSON body to `InventoryItemViewSet`.
- Validation: `InventoryItemSerializer.validate`.
- Persistence: `serializer.save()`.
- Side effect: `create_inventory_audit_log(...)` with `item_snapshot(...)`.

## 2) Inventory Bulk Import Pipeline (`/inventory-items/bulk-import/`)
```text
CSV file upload
-> decode + DictReader rows
-> row-to-payload mapping
-> per-row serializer validation
-> save valid rows
-> per-row audit log
-> aggregate result {created, failed, errors}
```

Observed behavior:
- Row errors are accumulated; processing continues for other rows.
- Pipeline output is summary JSON instead of single-record response.

## 3) Consumable Stock Transaction Pipeline
```text
HTTP POST stock transaction
-> serializer validate_quantity
-> atomic create()
   -> read stock
   -> compute new balance by transaction type
   -> reject if insufficient quantity
   -> update stock.quantity
   -> create transaction with balance_after
-> view perform_create
   -> set performed_by
   -> create audit log
   -> optional low-stock email alert
-> response
```

Observed controls:
- Transactional integrity: `@transaction.atomic` in serializer `create`.
- Business rule: stock cannot go negative for `STOCK_OUT`/`DAMAGE`.
- External notification: email on threshold breach when recipients are configured.

## 4) Assignment Pipeline
```text
assignment request (single or bulk)
-> serializer validation (target user/office required, return rules)
-> save assignment
-> audit log write (ASSIGN or RETURN)
-> response or bulk summary
```

Observed in `actions/views.py`:
- Both single-create/update and CSV bulk-import produce audit records.
- Summary pipeline also exists (`summary-by-assignee`) as grouped output.

## 5) Audit Pipeline (Cross-Cutting)
```text
business event in inventory/actions
-> create_inventory_audit_log(...)
-> InventoryAuditLog row
-> later consumed by audit endpoints and report endpoints
```

Audit data is a downstream data source for:
- audit log API (`audit` app)
- recent activity report (`reports` app)

## 6) Read/Report/Export Pipeline
### Dashboard and report JSON
```text
request
-> scoped queryset per user office access
-> ORM filters/aggregations/annotations
-> structured JSON response
```

### Export pipelines
- CSV export: iterate queryset and write lines to `HttpResponse(text/csv)`.
- Excel export: build workbook (`openpyxl`) and stream `.xlsx` response.
- PDF export: draw report rows via `reportlab` canvas and stream `.pdf` response.

## 7) Initialization / Seed Pipeline
From management commands:
```text
seed_prd_data command
-> call seed_initial_categories
-> seed offices
-> seed users
-> seed custom fields
-> seed inventory (+ subtype records)
-> seed assignments
-> seed stock transactions
-> seed audit logs
```

Observed characteristics:
- Idempotent update-or-create style across multiple steps.
- Dry-run mode wraps in transaction and rolls back.
- Category seeding pipeline is separated into dedicated command.

## Common Pipeline Guards
- Permission guard: `IMSAccessPermission`
- Data visibility guard: `scope_queryset_by_user`
- Serializer guards: domain validation and quantity checks
- Database guards: model constraints and transaction blocks

## Pipeline Outputs
- Operational outputs:
  - resource JSON from CRUD endpoints
  - summary JSON from bulk/report endpoints
- Artifact outputs:
  - CSV/Excel/PDF report downloads
- Side-effect outputs:
  - audit rows
  - optional low-stock email notifications

## What Is Missing
- No asynchronous queue-based data pipeline is wired in visible app code.
- No stream/event processor module is present.

## Chapter 8 Outcome
You now have a full data pipeline view from ingest (JSON/CSV/commands) through validation, scoped persistence, audit/notification side effects, and final outputs (JSON and exported files).
