import gzip
import hashlib
import os
import subprocess
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.utils import timezone

from common.models import BackupRun, JobRunStatus, RestoreDrillRun


def _backup_root():
    configured = (getattr(settings, "BACKUP_ROOT", "") or "").strip()
    if configured:
        path = Path(configured)
    else:
        path = Path(settings.BASE_DIR) / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _prune_old_backups():
    retention_days = int(getattr(settings, "BACKUP_RETENTION_DAYS", 14))
    if retention_days <= 0:
        return
    cutoff = timezone.now() - timedelta(days=retention_days)
    stale = BackupRun.objects.filter(status=JobRunStatus.SUCCESS, finished_at__lt=cutoff)
    for run in stale:
        if run.backup_file:
            try:
                Path(run.backup_file).unlink(missing_ok=True)
            except OSError:
                pass


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
        run.status = JobRunStatus.SUCCESS
        run.backup_file = str(output_path)
        run.checksum_sha256 = checksum
        run.backup_size_bytes = output_path.stat().st_size
        run.metadata = {"filename": filename}
        run.finished_at = timezone.now()
        run.error_message = ""
        run.save(
            update_fields=[
                "status",
                "backup_file",
                "checksum_sha256",
                "backup_size_bytes",
                "metadata",
                "finished_at",
                "error_message",
            ]
        )
        _prune_old_backups()
    except Exception as exc:
        run.status = JobRunStatus.FAILED
        run.error_message = str(exc)[:2000]
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "error_message", "finished_at"])
        raise
    return run


def run_restore_drill(backup_run=None):
    if backup_run is None:
        backup_run = BackupRun.objects.filter(status=JobRunStatus.SUCCESS).order_by("-finished_at").first()
    if backup_run is None or not backup_run.backup_file:
        raise ValueError("No successful backup available for restore drill.")

    drill = RestoreDrillRun.objects.create(backup_run=backup_run, status=JobRunStatus.RUNNING)
    env = os.environ.copy()
    env["DEBUG"] = "1"
    env["SECRET_KEY"] = env.get("SECRET_KEY", "x" * 60)
    env["ALLOWED_HOSTS"] = env.get("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver,example.com")
    env["ALLOW_SQLITE_IN_PROD"] = "1"
    env.pop("DATABASE_URL", None)

    temp_db_path = Path(tempfile.gettempdir()) / f"ims-restore-drill-{drill.id}.sqlite3"
    env["SQLITE_DB_PATH"] = str(temp_db_path)

    manage_py = str(Path(settings.BASE_DIR) / "manage.py")
    try:
        subprocess.run([sys.executable, manage_py, "migrate", "--noinput"], env=env, check=True, capture_output=True, text=True)
        subprocess.run([sys.executable, manage_py, "loaddata", backup_run.backup_file], env=env, check=True, capture_output=True, text=True)
        verify = subprocess.run(
            [sys.executable, manage_py, "shell", "-c", "from inventory.models import InventoryItem; print(InventoryItem.objects.count())"],
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

        restored_items = int((verify.stdout or "0").strip().splitlines()[-1])
        drill.status = JobRunStatus.SUCCESS
        drill.details = {"restored_inventory_items": restored_items, "restore_db_path": str(temp_db_path)}
        drill.error_message = ""
        drill.finished_at = timezone.now()
        drill.save(update_fields=["status", "details", "error_message", "finished_at"])
    except Exception as exc:
        drill.status = JobRunStatus.FAILED
        drill.error_message = str(exc)[:2000]
        drill.finished_at = timezone.now()
        drill.save(update_fields=["status", "error_message", "finished_at"])
        raise
    finally:
        temp_db_path.unlink(missing_ok=True)

    return drill
