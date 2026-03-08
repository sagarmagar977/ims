# Chapter 3 — Folder Structure

## Build Roadmap Position
- Stage: Foundation
- You are here: Chapter 3
- Before this: Chapter 2
- After this: Chapter 4

## Learning Objectives
- Understand the top-level directory layout of this repository.
- Identify where runtime code, domain code, docs, and deployment files live.
- Learn how each Django app is internally organized.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
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
```

## Topic 2 — Actual Implementation (Exact Repo Code)
### File: `django_project/`
Not present in current project as a single code file. This is a directory reference.
```text
django_project\asgi.py
django_project\settings.py
django_project\urls.py
django_project\wsgi.py
django_project\__init__.py
```

### File: `users/`
Not present in current project as a single code file. This is a directory reference.
```text
users\admin.py
users\apps.py
users\models.py
users\serializers.py
users\tests.py
users\urls.py
users\views.py
users\__init__.py
users\migrations\0001_initial.py
users\migrations\0002_alter_user_role.py
users\migrations\0003_user_office.py
users\migrations\__init__.py
```

### File: `PRD/`
Not present in current project as a single code file. This is a directory reference.
```text
PRD\BACKEND_PRD_ALIGNMENT.md
PRD\PRD - IMS.md
PRD\PRD - IMS.pdf
PRD\IMS design\add Assignments.png
PRD\IMS design\Add Categories.png
PRD\IMS design\Assignments-1.png
PRD\IMS design\Assignments.png
PRD\IMS design\Audit Logs.png
PRD\IMS design\Categories.png
PRD\IMS design\Create Item-1.png
PRD\IMS design\Create Item.png
PRD\IMS design\Dashboard.png
PRD\IMS design\Filter.png
PRD\IMS design\Items-1.png
PRD\IMS design\Items.png
PRD\IMS design\Login.png
PRD\IMS design\Stock (Consumables)-1.png
PRD\IMS design\Stock (Consumables).png
```

### File: `project_docs/`
Not present in current project as a single code file. This is a directory reference.
```text
project_docs\CONTEXT_LOG.md
project_docs\IMS_PROJECT_DOCS.md
project_docs\PROGRESS.md
project_docs\SYLLABUS.md
project_docs\chapters\CH01_Project_Overview.md
project_docs\chapters\CH02_Architecture_Pattern.md
project_docs\chapters\CH03_Folder_Structure.md
project_docs\chapters\CH04_Technology_Stack.md
project_docs\chapters\CH05_Dependency_Graph.md
project_docs\chapters\CH06_Entry_Point_Analysis.md
project_docs\chapters\CH07_Request_Lifecycle.md
project_docs\chapters\CH08_Data_Pipeline.md
project_docs\chapters\CH09_State_Management_if_exists.md
project_docs\chapters\CH10_External_Integrations.md
project_docs\chapters\CH11_Core_Runtime_Deployment_Files.md
project_docs\chapters\CH12_Users_App_Files.md
project_docs\chapters\CH13_Hierarchy_App_Files.md
project_docs\chapters\CH14_Catalog_App_Files.md
project_docs\chapters\CH15_Inventory_App_Files.md
project_docs\chapters\CH16_Actions_App_Files.md
project_docs\chapters\CH17_Audit_App_Files.md
project_docs\chapters\CH18_Reports_App_Files.md
project_docs\chapters\CH19_Common_App_Files.md
project_docs\chapters\CH20_Migrations_Across_Apps.md
project_docs\chapters\CH21_Requirements_and_Product_Reference_Files.md
project_docs\chapters\CH22_Deep_Dive_djangoprojectsettingspy.md
project_docs\chapters\CH23_Deep_Dive_djangoprojecturlspy.md
project_docs\chapters\CH24_Deep_Dive_commonpermissionspy_and_commonaccesspy.md
project_docs\chapters\CH25_Deep_Dive_usersmodelspy_usersserializerspy_usersviewspy.md
project_docs\chapters\CH26_Deep_Dive_hierarchymodelspy_hierarchyviewspy.md
project_docs\chapters\CH27_Deep_Dive_catalogmodelspy_catalogviewspy_catalogserializerspy.md
project_docs\chapters\CH28_Deep_Dive_inventorymodelspy.md
project_docs\chapters\CH29_Deep_Dive_inventoryserializerspy.md
project_docs\chapters\CH30_Deep_Dive_inventoryviewspy.md
project_docs\chapters\CH31_Deep_Dive_actionsmodelspy_actionsserializerspy_actionsviewspy.md
project_docs\chapters\CH32_Deep_Dive_auditmodelspy_auditviewspy_auditutilspy.md
project_docs\chapters\CH33_Deep_Dive_reportsviewspy.md
project_docs\chapters\CH34_Deep_Dive_Seed_and_bootstrap_commands.md
project_docs\chapters\CH35_Deep_Dive_Test_Suite_and_smoketestpy.md
project_docs\chapters\CH36_Guided_Rebuild.md
project_docs\chapters\CH37_Architecture_Improvements.md
project_docs\chapters\CH38_Refactoring.md
project_docs\chapters\CH39_Performance_Review.md
```

## Rebuild Step (Hands-on Roadmap)
- Implement or review the files listed in this chapter only.
- Validate behavior discussed in the original chapter explanation.
- Confirm readiness for the next chapter transition.

## Chapter Summary
This chapter ties repository explanation to exact code references and prepares the next build step.

## Files Used
- `django_project/`
- `users/`
- `PRD/`
- `project_docs/`

