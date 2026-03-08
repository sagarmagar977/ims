# Chapter 3 — Folder Structure

## Learning Goals
- Understand the top-level directory layout of this repository.
- Identify where runtime code, domain code, docs, and deployment files live.
- Learn how each Django app is internally organized.

## Reference Files
- Repository root listing
- `django_project/`
- `users/`, `hierarchy/`, `catalog/`, `inventory/`, `actions/`, `audit/`, `reports/`, `common/`
- `PRD/`
- `project_docs/`

## Root-Level Structure (Observed)
- `.venv/` — local Python virtual environment.
- `django_project/` — Django project configuration package (settings/urls/asgi/wsgi).
- `users/`, `hierarchy/`, `catalog/`, `inventory/`, `actions/`, `audit/`, `reports/`, `common/` — core Django apps.
- `PRD/` — product and alignment documentation plus design image assets.
- `project_docs/` — learning course documents created in this workflow.
- `manage.py` — Django CLI entrypoint.
- `requirements.txt` — Python dependency list.
- `render.yaml`, `Procfile`, `gunicorn.conf.py` — deployment/runtime configuration.
- `db.sqlite3`, `db.sqlite3-journal` — local SQLite database artifacts.
- `.smoke_test.py` — local smoke test script.
- `data.json` — data file present in root.

## Django Project Package Structure
`django_project/` contains:
- `settings.py` — global configuration
- `urls.py` — top-level route composition
- `asgi.py` — ASGI app
- `wsgi.py` — WSGI app

## Standard App Structure Pattern
Most domain apps follow this repeatable shape:
- `models.py` — data model
- `serializers.py` — DRF serialization/validation (except `reports` has no serializers file)
- `views.py` — DRF viewsets/APIViews
- `urls.py` — route registration
- `tests.py` — app tests
- `admin.py` / `apps.py` / `__init__.py`
- `migrations/` — schema migration history

## App-Specific Structure Notes
- `catalog/management/commands/seed_initial_categories.py` exists.
- `common/management/commands/bootstrap_admin.py` and `seed_prd_data.py` exist.
- `audit/` includes `utils.py` for audit log helpers.
- `reports/` includes `models.py` but no report-specific serializers module.

## Documentation and Course Structure
- `PRD/` includes:
  - `PRD - IMS.md`
  - `PRD - IMS.pdf`
  - `BACKEND_PRD_ALIGNMENT.md`
  - `IMS design/` image assets
- `project_docs/` includes:
  - `SYLLABUS.md`
  - `PROGRESS.md`
  - `CONTEXT_LOG.md`
  - `IMS_PROJECT_DOCS.md`
  - `chapters/` (chapter-wise notes)

## Folder Organization Interpretation
The repository is organized as a conventional Django monolith:
- central project config package,
- multiple domain apps with consistent internal patterns,
- explicit migration history per app,
- separate deployment/config files at root,
- and separate product/course documentation directories.

## Chapter 3 Outcome
You can now navigate the repository quickly, identify where each concern lives, and predict where to look when studying models, endpoints, permissions, tests, and deployment behavior.
