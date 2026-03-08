# Chapter 21 — Requirements and Product Reference Files

## Build Roadmap Position
- Stage: Core Domain
- You are here: Chapter 21
- Before this: Chapter 20
- After this: Chapter 22

## Learning Objectives
- Connect implementation decisions to declared requirements.
- Identify current alignment status and known gaps.
- `requirements.txt`

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
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
```

## Topic 2 — Actual Implementation (Exact Repo Code)
### File: `requirements.txt`
```text
amqp==5.3.1
asgiref==3.11.1
attrs==25.4.0
billiard==4.2.4
celery==5.6.2
charset-normalizer==3.4.4
click==8.3.1
click-didyoumean==0.3.1
click-plugins==1.1.1.2
click-repl==0.3.0
colorama==0.4.6
Django==6.0.2
django-filter==25.2
django-storages==1.14.6
djangorestframework==3.16.1
djangorestframework_simplejwt==5.5.1
drf-spectacular==0.29.0
et_xmlfile==2.0.0
gunicorn==23.0.0
whitenoise==6.9.0
inflection==0.5.1
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
kombu==5.6.2
openpyxl==3.1.5
packaging==26.0
pillow==12.1.1
prompt_toolkit==3.0.52
psycopg2-binary==2.9.11
PyJWT==2.11.0
pypdf==6.7.3
python-dateutil==2.9.0.post0
PyYAML==6.0.3
redis==7.2.0
referencing==0.37.0
reportlab==4.4.10
rpds-py==0.30.0
six==1.17.0
sqlparse==0.5.5
tzdata==2025.3
tzlocal==5.3.1
uritemplate==4.2.0
vine==5.1.0
wcwidth==0.6.0

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `PRD/PRD - IMS.md`
```markdown


Terms of Reference
Design and Development of Inventory Management System (IMS)
Department of National ID and Civil Registration (DoNIDCR)
Ministry of Home Affairs, Government of Nepal
## 1. Background
The Department of National ID and Civil Registration (DoNIDCR) under the Ministry of Home
Affairs (MoHA) is responsible for the registration of vital events (births, deaths, marriages,
divorces, migrations), issuance of National Identity Smart Cards, and distribution of Social
Security Allowance (SSA) benefits.
DoNIDCR operates through:
â— Central office
â— 7 provincial offices
â— 753 local level offices (municipalities & rural municipalities)
â— Approximately 6,713 ward-level registration points
The department maintains a large inventory of fixed assets (laptops, desktops, printers,
scanners, furniture, biometric devices, etc.) and consumables (registration forms, stationery,
toners, ribbons, batteries, etc.) distributed across all levels. Currently, inventory is managed
through manual ledgers, scattered Excel files, and occasional physical verification, leading to:
â— Lack of real-time visibility
â— Difficulty tracking ownership (who holds which laptop/printer)
â— No centralized audit trail
â— Challenges in preparing fiscal-year reports for audits
â— Risk of loss, misuse or duplication of assets
A modern Inventory Management System (IMS) is required to bring transparency,
accountability, and efficiency in asset tracking and reporting across the entire department.
## 2. Objectives
The primary objective is to design, develop, deploy and support a secure, web-based Inventory
Management System that enables DoNIDCR to:
- Maintain a centralized, real-time inventory of all fixed assets and consumables
- Track ownership and location of every item down to employee / ward level
- Allow dynamic creation of categories with custom fields
- Support document upload (invoices, handover letters, damage photos)
- Generate fiscal-year and category-based reports with PDF/Excel export
- Provide full audit trail for every movement (assign, return, repair, dispose)

- Ensure role-based access aligned with DoNIDCR hierarchy (central â†’ provincial â†’
ward)
- Scope of Work
## 3.1 Core Functional Modules
## A. Category & Custom Field Management
â— Admin can create/edit categories (Laptop, Printer, Stationery, Furniture, Biometric
Device, etc.)
â— Define custom fields per category (e.g. RAM/Processor for laptops, Model/Ink type for
printers)
â— Fields support: text, number, date, dropdown, file, checkbox
â— Mark fields as required/unique
## B. Item & Stock Management
â— Create single or bulk items (CSV import)
â— Fixed assets: serial number, purchase date, warranty, invoice upload
â— Consumables: initial quantity, min threshold, reorder alert
â— Automatic low-stock notification (email to store keeper)
## C. Assignment & Return Workflow
â— Assign item to employee or location (ward/provincial office)
â— Record handover date, condition, signed letter (upload)
â— Return flow with condition check & damage photo upload
â— Prevent double assignment
## D. Movement & Audit Trail
â— Log every action (assign/return/repair/dispose) with user, timestamp, before/after values
â— Support remarks and attachments
## E. Reporting & Export
â— Pre-defined reports:
â—‹ Inventory by fiscal year
â—‹ Assigned items by employee/ward/province
â—‹ Disposal history
â—‹ Low stock alerts
â— Filters: category, fiscal year, status, location
â— Export: PDF (with DoNIDCR letterhead), Excel
F. Role-Based Access Control

â— Super Admin (Central) â†’ full access
â— Central Procurement/Store â†’ bulk entry, dispatch
â— Provincial Admin â†’ provincial + ward items
â— Ward Officer â†’ only own ward items
â— Finance/Audit â†’ read-only reports + payment view
3.2 Non-Functional Requirements
â— Web-based, responsive (desktop + tablet)
â— Nepali + English interface
â— Support ~7,000 ward users (read-heavy)
â— HTTPS, role-based access, audit logging
â— Document storage: secure, versioned, searchable
â— Offline support (progressive web app) for ward offices with poor connectivity
â— Backup: daily automated backups
â— Uptime: 99.5% on government working days
## 3.3 Deliverables
â— Fully functional web application
â— Source code (Git repository)
â— Database schema & sample data
â— User manual (Nepali + English)
â— Administrator guide
â— Deployment guide (server setup, CI/CD)
â— Training for central & provincial staff (virtual + on-site)
â— 6 months warranty & support after go-live
- Services to be provided by Client (DoNIDCR)
â— Provide employee master list (CSV/API)
â— Share fiscal year calendar & chart of accounts
â— Provide sample asset data & document formats
â— Designate focal persons per province & central office
â— Facilitate access to central/provincial/ward offices for training & pilot
â— Provide test environment for integration (if existing HR/asset system)
## 5. Duration & Timeline
â— Total duration: 4â€“6 months
â— Suggested breakdown:
â—‹ Month 1: Requirement finalisation, wireframes, database design
â—‹ Month 2â€“3: Development & internal testing
â—‹ Month 4: UAT, training, pilot in 5â€“10 wards
â—‹ Month 5â€“6: Full rollout, handover & support

- Qualification of Consulting Firm
â— Minimum 3 years in web application development
â— Completed at least 3 government / large-scale inventory/ERP projects
â— Team must include: Project Manager (10+ years), System Architect (5+ years), Full-stack
Developer (3+ years), Database Expert, UI/UX Designer, QA Engineer
## 7. Ownership
DoNIDCR will have full ownership of source code, database, documents and any other
deliverables.
## 8. Progress Reporting
Consultant shall submit bi-weekly progress reports (every 15 days) in agreed format.
## 9. Payment Terms
To be mutually agreed (milestone-based recommended).
## 10. Acceptance & Sign-off
Final acceptance after successful UAT, pilot rollout and training completion.

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `PRD/BACKEND_PRD_ALIGNMENT.md`
```markdown
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

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

### File: `PRD/PRD - IMS.pdf`
Not present in current project as extractable text code. Binary PDF file.

### File: `data.json`
```json
[{"model": "sessions.session", "pk": "ittx7m0lcf4q57wxri48abi74oj03grz", "fields": {"session_data": ".eJxVjMsKwjAQAP9lzxKypHn16N1vCLt5mKok0LQn8d-l0INeZ4Z5Q6B9q2EfeQ1LghkQLr-MKT5zO0R6ULt3EXvb1oXFkYjTDnHrKb-uZ_s3qDQqzODZs5tcStKZbLU1VKiUSRZymqzKrNh4ExGNJY-xWGRU2kWrpYwOC3y-8I835Q:1vvtAw:Ki7V1QoEStuOQKf3_Dxv-K1bfqbVqRNtyx4RwQIwYBA", "expire_date": "2026-03-13T08:26:18.094Z"}}, {"model": "hierarchy.office", "pk": 1, "fields": {"name": "DoNIDCR Central Office", "level": "CENTRAL", "parent_office": null, "location_code": "NPL-CENTRAL-001"}}, {"model": "hierarchy.office", "pk": 2, "fields": {"name": "Province 1 Office", "level": "PROVINCIAL", "parent_office": 1, "location_code": "NPL-P1-001"}}, {"model": "hierarchy.office", "pk": 3, "fields": {"name": "Province 2 Office", "level": "PROVINCIAL", "parent_office": 1, "location_code": "NPL-P2-001"}}, {"model": "hierarchy.office", "pk": 4, "fields": {"name": "Kathmandu Metropolitan Office", "level": "LOCAL", "parent_office": 2, "location_code": "NPL-L1-001"}}, {"model": "hierarchy.office", "pk": 5, "fields": {"name": "Lalitpur Metropolitan Office", "level": "LOCAL", "parent_office": 2, "location_code": "NPL-L1-002"}}, {"model": "hierarchy.office", "pk": 6, "fields": {"name": "Ward 1 Registration Point", "level": "WARD", "parent_office": 4, "location_code": "NPL-W1-001"}}, {"model": "hierarchy.office", "pk": 7, "fields": {"name": "Ward 2 Registration Point", "level": "WARD", "parent_office": 4, "location_code": "NPL-W1-002"}}, {"model": "catalog.category", "pk": 1, "fields": {"name": "string", "is_consumable": true}}, {"model": "catalog.category", "pk": 2, "fields": {"name": "Laptop", "is_consumable": false}}, {"model": "catalog.category", "pk": 3, "fields": {"name": "Desktop", "is_consumable": false}}, {"model": "catalog.category", "pk": 4, "fields": {"name": "Printer", "is_consumable": false}}, {"model": "catalog.category", "pk": 5, "fields": {"name": "Scanner", "is_consumable": false}}, {"model": "catalog.category", "pk": 6, "fields": {"name": "Biometric Device", "is_consumable": false}}, {"model": "catalog.category", "pk": 7, "fields": {"name": "Furniture", "is_consumable": false}}, {"model": "catalog.category", "pk": 8, "fields": {"name": "Networking Equipment", "is_consumable": false}}, {"model": "catalog.category", "pk": 9, "fields": {"name": "UPS/Inverter", "is_consumable": false}}, {"model": "catalog.category", "pk": 10, "fields": {"name": "Server/Storage", "is_consumable": false}}, {"model": "catalog.category", "pk": 11, "fields": {"name": "CCTV/Access Device", "is_consumable": false}}, {"model": "catalog.category", "pk": 12, "fields": {"name": "Registration Forms", "is_consumable": true}}, {"model": "catalog.category", "pk": 13, "fields": {"name": "Stationery", "is_consumable": true}}, {"model": "catalog.category", "pk": 14, "fields": {"name": "Toner/Ink", "is_consumable": true}}, {"model": "catalog.category", "pk": 15, "fields": {"name": "Printer Ribbon", "is_consumable": true}}, {"model": "catalog.category", "pk": 16, "fields": {"name": "Batteries", "is_consumable": true}}, {"model": "catalog.category", "pk": 17, "fields": {"name": "Cables/Connectors", "is_consumable": true}}, {"model": "catalog.category", "pk": 18, "fields": {"name": "Cleaning/Repair Consumables", "is_consumable": true}}, {"model": "catalog.category", "pk": 19, "fields": {"name": "ID Card Consumables", "is_consumable": true}}, {"model": "catalog.customfielddefinition", "pk": 1, "fields": {"category": 2, "label": "RAM", "field_type": "SELECT", "required": true, "is_unique": false, "select_options": ["8GB", "16GB", "32GB"]}}, {"model": "catalog.customfielddefinition", "pk": 2, "fields": {"category": 2, "label": "Processor", "field_type": "TEXT", "required": true, "is_unique": false, "select_options": []}}, {"model": "catalog.customfielddefinition", "pk": 3, "fields": {"category": 2, "label": "Storage", "field_type": "SELECT", "required": true, "is_unique": false, "select_options": ["256GB SSD", "512GB SSD", "1TB SSD"]}}, {"model": "catalog.customfielddefinition", "pk": 4, "fields": {"category": 4, "label": "Model", "field_type": "TEXT", "required": true, "is_unique": false, "select_options": []}}, {"model": "catalog.customfielddefinition", "pk": 5, "fields": {"category": 4, "label": "Ink Type", "field_type": "SELECT", "required": true, "is_unique": false, "select_options": ["Inkjet", "Laser Toner"]}}, {"model": "catalog.customfielddefinition", "pk": 6, "fields": {"category": 6, "label": "Vendor", "field_type": "TEXT", "required": true, "is_unique": false, "select_options": []}}, {"model": "catalog.customfielddefinition", "pk": 7, "fields": {"category": 12, "label": "Form Type", "field_type": "SELECT", "required": true, "is_unique": false, "select_options": ["Birth", "Death", "Marriage"]}}, {"model": "catalog.customfielddefinition", "pk": 8, "fields": {"category": 13, "label": "Unit", "field_type": "TEXT", "required": true, "is_unique": false, "select_options": []}}, {"model": "catalog.customfielddefinition", "pk": 9, "fields": {"category": 14, "label": "Color", "field_type": "SELECT", "required": false, "is_unique": false, "select_options": ["Black", "Cyan", "Magenta", "Yellow"]}}, {"model": "inventory.inventoryitem", "pk": 1, "fields": {"category": 2, "office": 6, "title": "Dell Latitude 5440", "item_number": "FA-0001", "item_type": "FIXED_ASSET", "status": "ACTIVE", "image": "", "amount": "120000.00", "price": "120000.00", "currency": "NPR", "store": "", "project": "", "department": "Registration", "manufacturer": "Dell", "purchased_date": "2025-07-20", "pi_document": "", "warranty_document": "", "description": "", "dynamic_data": {"RAM": "16GB", "Processor": "Intel i7", "Storage": "512GB SSD"}, "created_at": "2026-02-26T06:27:06.772Z", "updated_at": "2026-02-26T06:27:06.773Z"}}, {"model": "inventory.inventoryitem", "pk": 2, "fields": {"category": 4, "office": 4, "title": "HP LaserJet Pro", "item_number": "FA-0002", "item_type": "FIXED_ASSET", "status": "ACTIVE", "image": "", "amount": "45000.00", "price": "45000.00", "currency": "NPR", "store": "", "project": "", "department": "Office Operations", "manufacturer": "HP", "purchased_date": "2025-08-10", "pi_document": "", "warranty_document": "", "description": "", "dynamic_data": {"Model": "M404dn", "Ink Type": "Laser Toner"}, "created_at": "2026-02-26T06:27:06.779Z", "updated_at": "2026-02-26T06:27:06.780Z"}}, {"model": "inventory.inventoryitem", "pk": 3, "fields": {"category": 12, "office": 6, "title": "Citizen Registration Form", "item_number": "CON-0001", "item_type": "CONSUMABLE", "status": "ACTIVE", "image": "", "amount": "10000.00", "price": "10.00", "currency": "NPR", "store": "", "project": "", "department": "Registration", "manufacturer": "Govt Printing Press", "purchased_date": "2025-07-25", "pi_document": "", "warranty_document": "", "description": "", "dynamic_data": {"Form Type": "Birth"}, "created_at": "2026-02-26T06:27:06.784Z", "updated_at": "2026-02-26T06:27:06.784Z"}}, {"model": "inventory.inventoryitem", "pk": 4, "fields": {"category": 13, "office": 4, "title": "A4 Office Paper", "item_number": "CON-0002", "item_type": "CONSUMABLE", "status": "ACTIVE", "image": "", "amount": "15000.00", "price": "500.00", "currency": "NPR", "store": "", "project": "", "department": "Admin", "manufacturer": "Nepal Paper Co", "purchased_date": "2025-09-01", "pi_document": "", "warranty_document": "", "description": "", "dynamic_data": {"Unit": "ream"}, "created_at": "2026-02-26T06:27:06.790Z", "updated_at": "2026-02-26T06:27:06.790Z"}}, {"model": "inventory.inventoryitem", "pk": 5, "fields": {"category": 2, "office": 1, "title": "HP pavelion", "item_number": "co-i9", "item_type": "FIXED_ASSET", "status": "ACTIVE", "image": "", "amount": "3.00", "price": "98000.00", "currency": "NPR", "store": "", "project": "", "department": "", "manufacturer": "HP", "purchased_date": null, "pi_document": "", "warranty_document": "", "description": "", "dynamic_data": {"RAM": "16GB", "Processor": "Intel i7", "Storage": "512GB SSD"}, "created_at": "2026-02-26T06:41:57.804Z", "updated_at": "2026-02-26T06:43:38.265Z"}}, {"model": "inventory.fixedasset", "pk": 1, "fields": {"item": 1, "asset_tag": "LAP-W1-0001", "serial_number": "SN-LAP-0001", "purchase_date": "2025-07-20", "warranty_expiry_date": "2028-07-20", "invoice_file": ""}}, {"model": "inventory.fixedasset", "pk": 2, "fields": {"item": 2, "asset_tag": "PRN-L1-0001", "serial_number": "SN-PRN-0001", "purchase_date": "2025-08-10", "warranty_expiry_date": "2027-08-10", "invoice_file": ""}}, {"model": "inventory.consumablestock", "pk": 1, "fields": {"item": 3, "initial_quantity": "1000.00", "quantity": "920.00", "min_threshold": "200.00", "reorder_alert_enabled": true, "unit": "pcs"}}, {"model": "inventory.consumablestock", "pk": 2, "fields": {"item": 4, "initial_quantity": "100.00", "quantity": "60.00", "min_threshold": "20.00", "reorder_alert_enabled": true, "unit": "ream"}}, {"model": "users.user", "fields": {"password": "pbkdf2_sha256$1200000$bGNMyIuQHHy6gWhnVlM3GV$dLxtC09kO5Ouy9ExSoafdcCP1qNZxQ5bydOSOd4sma4=", "last_login": "2026-02-27T08:26:18.088Z", "is_superuser": true, "username": "sagar", "first_name": "", "last_name": "", "email": "sagar@gmail.com", "is_staff": true, "is_active": true, "date_joined": "2026-02-25T18:41:06.338Z", "full_name_nepali": null, "role": null, "office": null, "groups": [], "user_permissions": []}}, {"model": "users.user", "fields": {"password": "pbkdf2_sha256$1200000$0EGUiw9Vb9Ix4UbiIiKOPd$Gw5DzJ255QZa8+uEymejAdbEgwLJyKNq4Neg4ChqB1U=", "last_login": null, "is_superuser": false, "username": "superadmin", "first_name": "Superadmin", "last_name": "", "email": "superadmin@ims.local", "is_staff": true, "is_active": true, "date_joined": "2026-02-26T06:26:48.447Z", "full_name_nepali": null, "role": "SUPER_ADMIN", "office": 1, "groups": [], "user_permissions": []}}, {"model": "users.user", "fields": {"password": "pbkdf2_sha256$1200000$H1xlm2QvSVUIug5NrxGB5F$14turiuSnq+3qwttyyjv/ZszCQITNZTn9aQR4Fql6vI=", "last_login": null, "is_superuser": false, "username": "central_admin", "first_name": "Central Admin", "last_name": "", "email": "central_admin@ims.local", "is_staff": true, "is_active": true, "date_joined": "2026-02-26T06:26:50.665Z", "full_name_nepali": null, "role": "CENTRAL_ADMIN", "office": 1, "groups": [], "user_permissions": []}}, {"model": "users.user", "fields": {"password": "pbkdf2_sha256$1200000$0UEneGklrnJ6NwvCavmh5E$p4a82ZGY1bLWAdlQVR9/DCqVYHURpcjMUTbxrZKet6g=", "last_login": null, "is_superuser": false, "username": "store_keeper", "first_name": "Store Keeper", "last_name": "", "email": "store_keeper@ims.local", "is_staff": false, "is_active": true, "date_joined": "2026-02-26T06:26:53.307Z", "full_name_nepali": null, "role": "CENTRAL_PROCUREMENT_STORE", "office": 1, "groups": [], "user_permissions": []}}, {"model": "users.user", "fields": {"password": "pbkdf2_sha256$1200000$1tty8jeqy5PXQTRxi5tClD$XVAspJZHBfqUXSgTW+bJeLaorbujvxIFc91UZJcxznQ=", "last_login": null, "is_superuser": false, "username": "prov_admin_p1", "first_name": "Prov Admin P1", "last_name": "", "email": "prov_admin_p1@ims.local", "is_staff": false, "is_active": true, "date_joined": "2026-02-26T06:26:55.591Z", "full_name_nepali": null, "role": "PROVINCIAL_ADMIN", "office": 2, "groups": [], "user_permissions": []}}, {"model": "users.user", "fields": {"password": "pbkdf2_sha256$1200000$YJoIiHnm50zTGE1V5XhfG1$0+uEh4yK9Q8nwWWqPrFPUyoVnRhPzOGtv3Sg7rmFsOA=", "last_login": null, "is_superuser": false, "username": "local_admin_ktm", "first_name": "Local Admin Ktm", "last_name": "", "email": "local_admin_ktm@ims.local", "is_staff": false, "is_active": true, "date_joined": "2026-02-26T06:26:57.778Z", "full_name_nepali": null, "role": "LOCAL_ADMIN", "office": 4, "groups": [], "user_permissions": []}}, {"model": "users.user", "fields": {"password": "pbkdf2_sha256$1200000$w9kVUonbpsOF97SG6yA49u$VT2S5yRObLWsAAc9+Z6HjtVbf3TMAiVgMm+XI8VF8XE=", "last_login": null, "is_superuser": false, "username": "ward_officer_1", "first_name": "Ward Officer 1", "last_name": "", "email": "ward_officer_1@ims.local", "is_staff": false, "is_active": true, "date_joined": "2026-02-26T06:26:59.934Z", "full_name_nepali": null, "role": "WARD_OFFICER", "office": 6, "groups": [], "user_permissions": []}}, {"model": "users.user", "fields": {"password": "pbkdf2_sha256$1200000$JwWMzis4skVYnfgIe8mzkv$BDN/87AyBUbXE/cLlWCguE7qTFijwrjfAvqyJdkfMnA=", "last_login": null, "is_superuser": false, "username": "finance_user", "first_name": "Finance User", "last_name": "", "email": "finance_user@ims.local", "is_staff": false, "is_active": true, "date_joined": "2026-02-26T06:27:02.166Z", "full_name_nepali": null, "role": "FINANCE", "office": 1, "groups": [], "user_permissions": []}}, {"model": "users.user", "fields": {"password": "pbkdf2_sha256$1200000$4eJUT8YcSwRR1PzqxXkPXd$bHrxvpuCNUc0RmjiQz8VO5jbMEAxI+4BC3JCsZk6MXk=", "last_login": null, "is_superuser": false, "username": "audit_user", "first_name": "Audit User", "last_name": "", "email": "audit_user@ims.local", "is_staff": false, "is_active": true, "date_joined": "2026-02-26T06:27:04.539Z", "full_name_nepali": null, "role": "AUDIT", "office": 1, "groups": [], "user_permissions": []}}, {"model": "admin.logentry", "pk": 1, "fields": {"action_time": "2026-02-26T06:41:57.824Z", "user": ["sagar"], "content_type": ["inventory", "inventoryitem"], "object_id": "5", "object_repr": "HP pavelion @ DoNIDCR Central Office (CENTRAL)", "action_flag": 1, "change_message": "[{\"added\": {}}]"}}, {"model": "admin.logentry", "pk": 2, "fields": {"action_time": "2026-02-26T06:43:38.272Z", "user": ["sagar"], "content_type": ["inventory", "inventoryitem"], "object_id": "5", "object_repr": "HP pavelion @ DoNIDCR Central Office (CENTRAL)", "action_flag": 2, "change_message": "[{\"changed\": {\"fields\": [\"Manufacturer\", \"Dynamic data\"]}}]"}}, {"model": "inventory.consumablestocktransaction", "pk": 1, "fields": {"stock": 1, "transaction_type": "STOCK_IN", "quantity": "1000.00", "balance_after": "1000.00", "status": "COMPLETED", "amount": "10000.00", "assigned_to": null, "department": "Central Store", "description": "PRD seed opening stock adjustment", "image": "", "performed_by": ["store_keeper"], "created_at": "2026-02-26T06:27:06.804Z"}}, {"model": "inventory.consumablestocktransaction", "pk": 2, "fields": {"stock": 1, "transaction_type": "STOCK_OUT", "quantity": "80.00", "balance_after": "920.00", "status": "COMPLETED", "amount": "800.00", "assigned_to": ["ward_officer_1"], "department": "Ward Services", "description": "PRD seed issued to ward office", "image": "", "performed_by": ["store_keeper"], "created_at": "2026-02-26T06:27:06.807Z"}}, {"model": "actions.itemassignment", "pk": 1, "fields": {"item": 1, "assigned_to_user": ["ward_officer_1"], "assigned_to_office": null, "assigned_by": ["store_keeper"], "handover_date": "2025-08-01", "assign_till": "2026-08-01", "handover_condition": "GOOD", "handover_letter": "", "status": "ASSIGNED", "returned_at": null, "return_condition": null, "damage_photo": "", "remarks": "PRD seed: assigned laptop to ward officer", "created_at": "2026-02-26T06:27:06.794Z"}}, {"model": "actions.itemassignment", "pk": 2, "fields": {"item": 2, "assigned_to_user": null, "assigned_to_office": 4, "assigned_by": ["store_keeper"], "handover_date": "2025-08-12", "assign_till": "2025-12-31", "handover_condition": "GOOD", "handover_letter": "", "status": "RETURNED", "returned_at": "2025-12-20T10:30:00Z", "return_condition": "GOOD", "damage_photo": "", "remarks": "PRD seed: printer returned in good condition", "created_at": "2026-02-26T06:27:06.799Z"}}, {"model": "audit.inventoryauditlog", "pk": 1, "fields": {"item": 1, "action_type": "CREATE", "performed_by": ["store_keeper"], "before_data": {}, "after_data": {"item_number": "FA-0001", "title": "Dell Latitude 5440", "status": "ACTIVE", "item_type": "FIXED_ASSET"}, "remarks": "PRD seed: created FA-0001", "attachment": "", "created_at": "2026-02-26T06:27:06.809Z"}}, {"model": "audit.inventoryauditlog", "pk": 2, "fields": {"item": 2, "action_type": "CREATE", "performed_by": ["store_keeper"], "before_data": {}, "after_data": {"item_number": "FA-0002", "title": "HP LaserJet Pro", "status": "ACTIVE", "item_type": "FIXED_ASSET"}, "remarks": "PRD seed: created FA-0002", "attachment": "", "created_at": "2026-02-26T06:27:06.812Z"}}, {"model": "audit.inventoryauditlog", "pk": 3, "fields": {"item": 3, "action_type": "CREATE", "performed_by": ["store_keeper"], "before_data": {}, "after_data": {"item_number": "CON-0001", "title": "Citizen Registration Form", "status": "ACTIVE", "item_type": "CONSUMABLE"}, "remarks": "PRD seed: created CON-0001", "attachment": "", "created_at": "2026-02-26T06:27:06.815Z"}}, {"model": "audit.inventoryauditlog", "pk": 4, "fields": {"item": 4, "action_type": "CREATE", "performed_by": ["store_keeper"], "before_data": {}, "after_data": {"item_number": "CON-0002", "title": "A4 Office Paper", "status": "ACTIVE", "item_type": "CONSUMABLE"}, "remarks": "PRD seed: created CON-0002", "attachment": "", "created_at": "2026-02-26T06:27:06.817Z"}}, {"model": "audit.inventoryauditlog", "pk": 5, "fields": {"item": 1, "action_type": "ASSIGN", "performed_by": ["store_keeper"], "before_data": {}, "after_data": {"status": "ASSIGNED"}, "remarks": "PRD seed: assignment recorded", "attachment": "", "created_at": "2026-02-26T06:27:06.819Z"}}, {"model": "audit.inventoryauditlog", "pk": 6, "fields": {"item": 2, "action_type": "RETURN", "performed_by": ["store_keeper"], "before_data": {}, "after_data": {"status": "RETURNED"}, "remarks": "PRD seed: return recorded", "attachment": "", "created_at": "2026-02-26T06:27:06.821Z"}}]

```

### Annotated Notes
- Why used: this file is part of the chapter scope and repository flow at this stage.
- What to inspect: imports, model/view/serializer/command classes, and function boundaries.
- How to study: read top-to-bottom once, then trace one request/data path through this file.
- Side effects: check for database writes, audit logging, notifications, exports, or permission gating.

## Rebuild Step (Hands-on Roadmap)
- Implement or review the files listed in this chapter only.
- Validate behavior discussed in the original chapter explanation.
- Confirm readiness for the next chapter transition.

## Chapter Summary
This chapter ties repository explanation to exact code references and prepares the next build step.

## Files Used
- `requirements.txt`
- `PRD/PRD - IMS.md`
- `PRD/BACKEND_PRD_ALIGNMENT.md`
- `PRD/PRD - IMS.pdf`
- `data.json`

