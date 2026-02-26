from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Category


FIXED_ASSET_CATEGORIES = [
    "Laptop",
    "Desktop",
    "Printer",
    "Scanner",
    "Biometric Device",
    "Furniture",
    "Networking Equipment",
    "UPS/Inverter",
    "Server/Storage",
    "CCTV/Access Device",
]

CONSUMABLE_CATEGORIES = [
    "Registration Forms",
    "Stationery",
    "Toner/Ink",
    "Printer Ribbon",
    "Batteries",
    "Cables/Connectors",
    "Cleaning/Repair Consumables",
    "ID Card Consumables",
]


class Command(BaseCommand):
    help = "Seed initial PRD-based catalog categories (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without writing to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        created = 0
        updated = 0
        unchanged = 0

        targets = [(name, False) for name in FIXED_ASSET_CATEGORIES] + [
            (name, True) for name in CONSUMABLE_CATEGORIES
        ]

        with transaction.atomic():
            for name, is_consumable in targets:
                obj = Category.objects.filter(name=name).first()
                if obj is None:
                    created += 1
                    if not dry_run:
                        Category.objects.create(name=name, is_consumable=is_consumable)
                    self.stdout.write(self.style.SUCCESS(f"{'Would create' if dry_run else 'Created'}: {name}"))
                    continue

                if obj.is_consumable != is_consumable:
                    updated += 1
                    if not dry_run:
                        obj.is_consumable = is_consumable
                        obj.save(update_fields=["is_consumable"])
                    self.stdout.write(self.style.WARNING(f"{'Would update' if dry_run else 'Updated'}: {name}"))
                else:
                    unchanged += 1
                    self.stdout.write(f"Unchanged: {name}")

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("Dry run enabled. Rolled back all changes."))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. created={created}, updated={updated}, unchanged={unchanged}, dry_run={dry_run}"
            )
        )
