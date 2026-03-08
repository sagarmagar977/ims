# Chapter 40 — Backend Operations and Hardening Update

## Build Roadmap Position
- Stage: Hardening
- You are here: Chapter 40
- Before this: Chapter 39
- After this: Ongoing operational maturity in target production infrastructure

## Learning Objectives
- Understand how async scheduling was extended beyond reporting into backup and SLO monitoring.
- Understand provider-backed notification delivery tracking and webhook-based status updates.
- Understand backup creation + restore drill orchestration and where execution evidence is stored.
- Understand new CI quality gates for lifecycle policy, security posture, and backup drills.

## Topic 1 — Chapter Guide
### What this is
This chapter documents the backend progress added after the initial 39-chapter pass.
### Why this exists in this project
The codebase now includes operational controls that were previously planned but not implemented.
### How it works here (actual flow)
The summary below maps directly to real files added or updated in this repository.

### Original Chapter Explanation
```markdown
# Chapter 40 — Backend Operations and Hardening Update

## What changed in this update
1. Scheduler/task expansion:
- Added periodic Celery tasks for:
  - low-stock alerts,
  - inventory summary generation,
  - database backups,
  - restore drills,
  - SLO monitoring.

2. Notification integration and delivery tracking:
- Added delivery model with status lifecycle (`QUEUED`, `SENT`, `DELIVERED`, `FAILED`).
- Added email provider modes (Django backend / SendGrid).
- Added SMS provider mode (Twilio).
- Added webhook endpoints for provider delivery status callbacks.

3. Backup and restore drill automation:
- Added backup artifact generation (`dumpdata` + gzip + checksum).
- Added restore drill into isolated temporary database and post-restore verification.
- Added run history tables and admin visibility.

4. Observability and SLO instrumentation:
- Added operational metrics builder.
- Added SLO breach evaluator with threshold-based checks.
- Added read endpoints for operational and SLO status.

5. CI and security hardening gates:
- Added endpoint lifecycle policy validation gate.
- Added security posture gate.
- Added migration + backup/restore drill checks in CI pipeline.
- Added dependency and static security workflow (`pip-audit`, `bandit`).

## Why this matters
- Moves non-functional requirements from documentation intent into executable controls.
- Adds repeatable operational evidence (backup history, drill history, CI gate results).
- Reduces regression risk on security and lifecycle policy.

## Chapter 40 Outcome
You can now trace how production-hardening concerns were implemented as first-class backend code, management commands, and CI gates.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
### File: `common/tasks.py`
```python
@shared_task
def periodic_database_backup():
    run = create_database_backup()
    return {
        "backup_run_id": run.id,
        "status": run.status,
        "backup_file": run.backup_file,
        "size_bytes": run.backup_size_bytes,
    }


@shared_task
def periodic_restore_drill():
    drill = run_restore_drill()
    return {
        "restore_drill_id": drill.id,
        "status": drill.status,
        "backup_run_id": drill.backup_run_id,
    }


@shared_task
def periodic_slo_monitor():
    metrics = current_operational_metrics()
    breaches = evaluate_slo_breaches(metrics=metrics)
    recipients = [email for email in getattr(settings, "OPS_ALERT_EMAILS", []) if email]
    if breaches and recipients:
        send_email_notification(
            subject="IMS SLO Alert",
            body="\n".join(["SLO breach detected:"] + [f"- {b}" for b in breaches]),
            recipients=recipients,
            metadata={"event": "slo_breach", "breaches": breaches, "metrics": metrics},
        )
    return {"breaches": breaches, "metrics": metrics}
```

### File: `common/notifications.py`
```python
def send_email_notification(subject, body, recipients, metadata=None):
    provider = getattr(settings, "NOTIFICATION_EMAIL_PROVIDER", "django").strip().lower()
    deliveries = []
    for recipient in recipients:
        if not recipient:
            continue
        delivery = NotificationDelivery.objects.create(
            channel=NotificationChannel.EMAIL,
            provider=provider,
            recipient=recipient,
            subject=subject[:255],
            message=body,
            metadata=_default_metadata(metadata),
        )
```

### File: `common/backups.py`
```python
def create_database_backup():
    run = BackupRun.objects.create(status=JobRunStatus.RUNNING)
    now = timezone.now()
    filename = f"ims-backup-{now.strftime('%Y%m%d-%H%M%S')}.json.gz"
    output_path = _backup_root() / filename
    try:
        with gzip.open(output_path, "wt", encoding="utf-8") as fh:
            call_command(
                "dumpdata",
                "--exclude=contenttypes",
                "--exclude=auth.permission",
                stdout=fh,
            )
        checksum = hashlib.sha256(output_path.read_bytes()).hexdigest()
```

### File: `common/observability.py`
```python
def current_operational_metrics():
    now = timezone.now()
    one_day_ago = now - timedelta(hours=24)
    backup = BackupRun.objects.filter(status=JobRunStatus.SUCCESS).order_by("-finished_at").first()
    drill = RestoreDrillRun.objects.order_by("-finished_at", "-started_at").first()
```

### File: `common/management/commands/run_backup.py`
```python
class Command(BaseCommand):
    help = "Create a database backup and track the run."

    def handle(self, *args, **options):
        run = create_database_backup()
        self.stdout.write(self.style.SUCCESS(f"Backup created: id={run.id} file={run.backup_file}"))
```

### File: `common/management/commands/run_restore_drill.py`
```python
class Command(BaseCommand):
    help = "Run a restore drill from the latest successful backup or specified backup id."
```

### File: `.github/workflows/ci.yml`
```yaml
      - name: Endpoint lifecycle gate
        run: python scripts/check_endpoint_lifecycle.py
      - name: Security posture gate
        run: python scripts/check_security_posture.py
      - name: Apply migrations
        run: python manage.py migrate --noinput
      - name: Backup orchestration drill
        run: |
          python manage.py run_backup
          python manage.py run_restore_drill
      - name: Run test suite
        run: python manage.py test
```

### File: `.github/workflows/security.yml`
```yaml
      - name: Dependency vulnerability audit
        run: pip-audit
      - name: Static security scan
        run: bandit -q -r users hierarchy catalog inventory actions audit reports common django_project
```

### File: `scripts/check_security_posture.py`
```python
if _strict_mode():
    if settings.DEBUG:
        errors.append("settings.DEBUG must be false in strict mode.")
    if settings.CORS_ALLOW_ALL_ORIGINS:
        errors.append("CORS_ALLOW_ALL_ORIGINS must be false in strict mode.")
```

## Rebuild Step (Hands-on Roadmap)
- Run migrations and verify new `common` and `reports` migration state.
- Run `python manage.py run_backup` and `python manage.py run_restore_drill`.
- Hit `GET /api/observability/status/` and `GET /api/observability/slo/` with auth.
- Run lifecycle and security scripts locally before pushing.

## Chapter Summary
This chapter captures the transition from planned hardening items to implemented backend operations code, with CI enforcement and operational run history.

## Files Used
- `common/models.py`
- `common/views.py`
- `common/urls.py`
- `common/admin.py`
- `common/tests.py`
- `common/notifications.py`
- `common/tasks.py`
- `common/backups.py`
- `common/observability.py`
- `common/management/commands/run_backup.py`
- `common/management/commands/run_restore_drill.py`
- `common/migrations/0001_initial.py`
- `common/migrations/0002_backuprun_restoredrillrun.py`
- `reports/models.py`
- `reports/admin.py`
- `reports/tests.py`
- `reports/migrations/0001_initial.py`
- `django_project/settings.py`
- `django_project/urls.py`
- `django_project/celery.py`
- `.github/workflows/ci.yml`
- `.github/workflows/security.yml`
- `scripts/check_endpoint_lifecycle.py`
- `scripts/check_security_posture.py`
- `PRD/ENDPOINT_LIFECYCLE_CALENDAR.json`
- `PRD/ENDPOINT_LIFECYCLE_CALENDAR.md`
- `PRD/BACKEND_OPERATIONS_RUNBOOK.md`
- `PRD/PRD_IMS_BACKEND_CROSSWALK.md`
