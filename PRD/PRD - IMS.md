

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
● Central office
● 7 provincial offices
● 753 local level offices (municipalities & rural municipalities)
● Approximately 6,713 ward-level registration points
The department maintains a large inventory of fixed assets (laptops, desktops, printers,
scanners, furniture, biometric devices, etc.) and consumables (registration forms, stationery,
toners, ribbons, batteries, etc.) distributed across all levels. Currently, inventory is managed
through manual ledgers, scattered Excel files, and occasional physical verification, leading to:
● Lack of real-time visibility
● Difficulty tracking ownership (who holds which laptop/printer)
● No centralized audit trail
● Challenges in preparing fiscal-year reports for audits
● Risk of loss, misuse or duplication of assets
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

- Ensure role-based access aligned with DoNIDCR hierarchy (central → provincial →
ward)
- Scope of Work
## 3.1 Core Functional Modules
## A. Category & Custom Field Management
● Admin can create/edit categories (Laptop, Printer, Stationery, Furniture, Biometric
Device, etc.)
● Define custom fields per category (e.g. RAM/Processor for laptops, Model/Ink type for
printers)
● Fields support: text, number, date, dropdown, file, checkbox
● Mark fields as required/unique
## B. Item & Stock Management
● Create single or bulk items (CSV import)
● Fixed assets: serial number, purchase date, warranty, invoice upload
● Consumables: initial quantity, min threshold, reorder alert
● Automatic low-stock notification (email to store keeper)
## C. Assignment & Return Workflow
● Assign item to employee or location (ward/provincial office)
● Record handover date, condition, signed letter (upload)
● Return flow with condition check & damage photo upload
● Prevent double assignment
## D. Movement & Audit Trail
● Log every action (assign/return/repair/dispose) with user, timestamp, before/after values
● Support remarks and attachments
## E. Reporting & Export
● Pre-defined reports:
○ Inventory by fiscal year
○ Assigned items by employee/ward/province
○ Disposal history
○ Low stock alerts
● Filters: category, fiscal year, status, location
● Export: PDF (with DoNIDCR letterhead), Excel
F. Role-Based Access Control

● Super Admin (Central) → full access
● Central Procurement/Store → bulk entry, dispatch
● Provincial Admin → provincial + ward items
● Ward Officer → only own ward items
● Finance/Audit → read-only reports + payment view
3.2 Non-Functional Requirements
● Web-based, responsive (desktop + tablet)
● Nepali + English interface
● Support ~7,000 ward users (read-heavy)
● HTTPS, role-based access, audit logging
● Document storage: secure, versioned, searchable
● Offline support (progressive web app) for ward offices with poor connectivity
● Backup: daily automated backups
● Uptime: 99.5% on government working days
## 3.3 Deliverables
● Fully functional web application
● Source code (Git repository)
● Database schema & sample data
● User manual (Nepali + English)
● Administrator guide
● Deployment guide (server setup, CI/CD)
● Training for central & provincial staff (virtual + on-site)
● 6 months warranty & support after go-live
- Services to be provided by Client (DoNIDCR)
● Provide employee master list (CSV/API)
● Share fiscal year calendar & chart of accounts
● Provide sample asset data & document formats
● Designate focal persons per province & central office
● Facilitate access to central/provincial/ward offices for training & pilot
● Provide test environment for integration (if existing HR/asset system)
## 5. Duration & Timeline
● Total duration: 4–6 months
● Suggested breakdown:
○ Month 1: Requirement finalisation, wireframes, database design
○ Month 2–3: Development & internal testing
○ Month 4: UAT, training, pilot in 5–10 wards
○ Month 5–6: Full rollout, handover & support

- Qualification of Consulting Firm
● Minimum 3 years in web application development
● Completed at least 3 government / large-scale inventory/ERP projects
● Team must include: Project Manager (10+ years), System Architect (5+ years), Full-stack
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
