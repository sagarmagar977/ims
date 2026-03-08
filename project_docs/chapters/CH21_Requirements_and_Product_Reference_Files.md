# Chapter 21 — Requirements and Product Reference Files

## Learning Goals
- Connect implementation decisions to declared requirements.
- Identify current alignment status and known gaps.

## Reference Files
- `requirements.txt`
- `PRD/PRD - IMS.md`
- `PRD/BACKEND_PRD_ALIGNMENT.md`
- `PRD/PRD - IMS.pdf`
- `data.json`

## File Breakdown

## 1) `requirements.txt`
- Core backend stack present:
  - Django, DRF, SimpleJWT, django-filter, drf-spectacular.
- Reporting/export libs present:
  - openpyxl, reportlab.
- Deployment/runtime libs present:
  - gunicorn, whitenoise, psycopg2-binary.
- Async-related packages present:
  - celery, redis, amqp/kombu/billiard.
- Observation from code: no Celery worker/task module is currently implemented.

## 2) `PRD/PRD - IMS.md` and `PRD/PRD - IMS.pdf`
- Define functional modules:
  - category/custom fields,
  - item/stock management,
  - assignment/return workflow,
  - audit trail,
  - reporting/export,
  - role-based access.
- Define non-functional expectations such as scale, security, and uptime.

## 3) `PRD/BACKEND_PRD_ALIGNMENT.md`
- Tracks implemented backend features and partial/missing items.
- Confirms completed items like RBAC matrix, audit logs, reports, exports, versioned API routing.
- Flags remaining items such as background jobs and deeper operational hardening.

## 4) `data.json`
- Snapshot fixture-like dataset containing offices, categories, custom fields, inventory items, users, assignments, stock transactions, and audit logs.
- Useful as learning sample for realistic relational data shape.

## Chapter 21 Outcome
You now understand the requirement baseline, the declared alignment status, and the exact package/features that are present versus missing in the current reference project.
