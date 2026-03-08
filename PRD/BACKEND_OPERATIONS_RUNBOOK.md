# Backend Operations Runbook

## Daily/Periodic Jobs
- Low stock alerts: Celery task `common.tasks.periodic_low_stock_alerts`
- Report generation: Celery task `common.tasks.periodic_inventory_report_generation`
- Database backup: Celery task `common.tasks.periodic_database_backup`
- Restore drill: Celery task `common.tasks.periodic_restore_drill`
- SLO monitor and alerting: Celery task `common.tasks.periodic_slo_monitor`

## Manual Commands
- Create backup: `python manage.py run_backup`
- Run restore drill: `python manage.py run_restore_drill`
- Run restore drill for a specific backup: `python manage.py run_restore_drill --backup-id <id>`

## Observability APIs
- Operational status: `GET /api/observability/status/` (and `/api/v1/observability/status/`)
- SLO status: `GET /api/observability/slo/` (and `/api/v1/observability/slo/`)

## Key Environment Variables
- `BACKUP_ROOT`, `BACKUP_RETENTION_DAYS`
- `BACKUP_INTERVAL_SECONDS`, `RESTORE_DRILL_INTERVAL_SECONDS`
- `OPS_ALERT_EMAILS`
- `SLO_BACKUP_MAX_AGE_HOURS`
- `SLO_MAX_FAILED_NOTIFICATIONS_24H`
- `SLO_REQUIRE_SUCCESSFUL_RESTORE_DRILL`
- `SLO_RESTORE_DRILL_MAX_AGE_DAYS`
- `NOTIFICATION_EMAIL_PROVIDER`, `NOTIFICATION_SMS_PROVIDER`
- `SENDGRID_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_PHONE`

## CI Gates
- Endpoint lifecycle gate: `scripts/check_endpoint_lifecycle.py`
- Security posture gate: `scripts/check_security_posture.py`
- Backup/restore drill gate: `manage.py run_backup` + `manage.py run_restore_drill`
- Dependency and static security scan: GitHub `security.yml` (`pip-audit`, `bandit`)
