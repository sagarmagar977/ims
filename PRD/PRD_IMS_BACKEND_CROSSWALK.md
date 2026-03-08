# PRD IMS Backend Crosswalk

Source: `PRD/PRD - IMS.md`

## Core Functional Modules
- Category & Custom Field Management: `Aligned`
- Item & Stock Management: `Aligned`
  - Includes low-stock alerts via scheduler + provider-backed notifications.
- Assignment & Return Workflow: `Aligned`
- Movement & Audit Trail: `Aligned`
- Reporting & Export: `Aligned`
  - Includes report generation job and PDF/Excel/CSV export APIs.
- Role-Based Access Control: `Aligned`

## Non-Functional Requirements (Backend Scope)
- HTTPS-ready and secure settings baseline: `Aligned` (deployment/env dependent for final enforcement)
- Role-based access + audit logging: `Aligned`
- Daily automated backup: `Aligned`
  - Backup scheduler + command + restore drill + CI drill gate added.
- Uptime target support (99.5%) instrumentation: `Partially Aligned`
  - SLO monitoring/alerts implemented; actual uptime SLA depends on production infra.
- Document storage secure/versioned/searchable: `Partially Aligned`
  - Secure upload paths and access controls exist; full versioned/search indexing backend not yet implemented.
- Offline support (PWA): `Out of Backend Scope` (frontend/client capability)
- Nepali + English interface: `Out of Backend Scope` (frontend/localization layer)

## Operational Deliverables Support
- Source code, schema, CI/CD hooks: `Aligned`
- Deployment/operations guidance: `Aligned` (`PRD/BACKEND_OPERATIONS_RUNBOOK.md`)
