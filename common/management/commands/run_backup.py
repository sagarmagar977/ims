from django.core.management.base import BaseCommand

from common.backups import create_database_backup


class Command(BaseCommand):
    help = "Create a database backup and track the run."

    def handle(self, *args, **options):
        run = create_database_backup()
        self.stdout.write(self.style.SUCCESS(f"Backup created: id={run.id} file={run.backup_file}"))
