from django.core.management.base import BaseCommand, CommandError

from common.backups import run_restore_drill
from common.models import BackupRun


class Command(BaseCommand):
    help = "Run a restore drill from the latest successful backup or specified backup id."

    def add_arguments(self, parser):
        parser.add_argument("--backup-id", type=int, default=None, help="Optional BackupRun id to use.")

    def handle(self, *args, **options):
        backup_id = options.get("backup_id")
        backup_run = None
        if backup_id:
            backup_run = BackupRun.objects.filter(id=backup_id).first()
            if backup_run is None:
                raise CommandError(f"BackupRun id={backup_id} not found.")
        drill = run_restore_drill(backup_run=backup_run)
        self.stdout.write(self.style.SUCCESS(f"Restore drill completed: id={drill.id} status={drill.status}"))
