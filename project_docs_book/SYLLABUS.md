# Project Course Syllabus

## Part I - System Foundations
### Chapter 1 - Project Overview
### Chapter 2 - Architecture Pattern
### Chapter 3 - Folder Structure
### Chapter 4 - Technology Stack
### Chapter 5 - Dependency Graph

## Part II - Data and Execution Flow
### Chapter 6 - Entry Point Analysis
### Chapter 7 - Request Lifecycle
### Chapter 8 - Data Pipeline
### Chapter 9 - State Management (if exists)
### Chapter 10 - External Integrations

## Part III - File Breakdown
### Chapter 11 - Core Runtime and Deployment Files (`manage.py`, `django_project/settings.py`, `django_project/urls.py`, `django_project/asgi.py`, `django_project/wsgi.py`, `gunicorn.conf.py`, `Procfile`, `render.yaml`, `.smoke_test.py`)
### Chapter 12 - Users App Files (`users/models.py`, `users/serializers.py`, `users/views.py`, `users/urls.py`, `users/tests.py`, `users/admin.py`, `users/apps.py`)
### Chapter 13 - Hierarchy App Files (`hierarchy/models.py`, `hierarchy/serializers.py`, `hierarchy/views.py`, `hierarchy/urls.py`, `hierarchy/tests.py`, `hierarchy/admin.py`, `hierarchy/apps.py`)
### Chapter 14 - Catalog App Files (`catalog/models.py`, `catalog/serializers.py`, `catalog/views.py`, `catalog/urls.py`, `catalog/tests.py`, `catalog/admin.py`, `catalog/apps.py`, `catalog/management/commands/seed_initial_categories.py`)
### Chapter 15 - Inventory App Files (`inventory/models.py`, `inventory/serializers.py`, `inventory/views.py`, `inventory/urls.py`, `inventory/tests.py`, `inventory/admin.py`, `inventory/apps.py`)
### Chapter 16 - Actions App Files (`actions/models.py`, `actions/serializers.py`, `actions/views.py`, `actions/urls.py`, `actions/tests.py`, `actions/admin.py`, `actions/apps.py`)
### Chapter 17 - Audit App Files (`audit/models.py`, `audit/serializers.py`, `audit/views.py`, `audit/urls.py`, `audit/utils.py`, `audit/tests.py`, `audit/admin.py`, `audit/apps.py`)
### Chapter 18 - Reports App Files (`reports/views.py`, `reports/urls.py`, `reports/models.py`, `reports/tests.py`, `reports/admin.py`, `reports/apps.py`)
### Chapter 19 - Common App Files (`common/access.py`, `common/permissions.py`, `common/middleware.py`, `common/views.py`, `common/models.py`, `common/tests.py`, `common/admin.py`, `common/apps.py`, `common/management/commands/bootstrap_admin.py`, `common/management/commands/seed_prd_data.py`)
### Chapter 20 - Migrations Across Apps (`users/migrations/*`, `hierarchy/migrations/*`, `catalog/migrations/*`, `inventory/migrations/*`, `actions/migrations/*`, `audit/migrations/*`)
### Chapter 21 - Requirements and Product Reference Files (`requirements.txt`, `PRD/PRD - IMS.md`, `PRD/BACKEND_PRD_ALIGNMENT.md`, `PRD/PRD - IMS.pdf`, `data.json`)

## Part IV - Line-by-Line Deep Dive
### Chapter 22 - Deep Dive: `django_project/settings.py`
### Chapter 23 - Deep Dive: `django_project/urls.py`
### Chapter 24 - Deep Dive: `common/permissions.py` and `common/access.py`
### Chapter 25 - Deep Dive: `users/models.py`, `users/serializers.py`, `users/views.py`
### Chapter 26 - Deep Dive: `hierarchy/models.py`, `hierarchy/views.py`
### Chapter 27 - Deep Dive: `catalog/models.py`, `catalog/views.py`, `catalog/serializers.py`
### Chapter 28 - Deep Dive: `inventory/models.py` (domain model and constraints)
### Chapter 29 - Deep Dive: `inventory/serializers.py` (validation and stock mutation)
### Chapter 30 - Deep Dive: `inventory/views.py` (CRUD, bulk import, audit hooks, low-stock email)
### Chapter 31 - Deep Dive: `actions/models.py`, `actions/serializers.py`, `actions/views.py`
### Chapter 32 - Deep Dive: `audit/models.py`, `audit/views.py`, `audit/utils.py`
### Chapter 33 - Deep Dive: `reports/views.py` and export/report generation paths
### Chapter 34 - Deep Dive: Seed and bootstrap commands (`common/management/commands/*.py`, `catalog/management/commands/seed_initial_categories.py`)
### Chapter 35 - Deep Dive: Test Suite (`*/tests.py`) and `.smoke_test.py`

## Part V - Rebuild and Refactor
### Chapter 36 - Guided Rebuild
### Chapter 37 - Architecture Improvements
### Chapter 38 - Refactoring
### Chapter 39 - Performance Review
### Chapter 40 - Backend Operations and Hardening Update

- Total Chapters: 40
- Estimated Learning Stages: 6 stages (Foundations, Flow, Module Breakdown, Deep Dive I, Deep Dive II, Rebuild/Refactor)
