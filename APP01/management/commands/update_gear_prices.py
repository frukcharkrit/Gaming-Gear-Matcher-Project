"""
Django management command to update all GamingGear prices.
Uses brand+category defaults with specific model overrides.

Usage:
    python manage.py update_gear_prices          # dry-run (preview)
    python manage.py update_gear_prices --apply   # actually update DB
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from APP01.models import GamingGear
from APP01.management.commands.gear_prices_data import (
    BRAND_CATEGORY_DEFAULTS,
    MODEL_OVERRIDES,
)


class Command(BaseCommand):
    help = "Populate price for all GamingGear items using market-researched data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually write prices to the database. Without this flag, runs in dry-run mode.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing non-null prices. Default: only update items with null price.",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        overwrite = options["overwrite"]

        if overwrite:
            gears = GamingGear.objects.all()
        else:
            gears = GamingGear.objects.filter(price__isnull=True)

        total = gears.count()
        updated = 0
        missing = 0

        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(f"  Gaming Gear Price Update")
        self.stdout.write(f"  Mode: {'APPLY' if apply else 'DRY-RUN (use --apply to save)'}")
        self.stdout.write(f"  Items to process: {total}")
        self.stdout.write(f"{'='*70}\n")

        missing_items = []

        for gear in gears:
            price = self._get_price(gear)
            if price is not None:
                if apply:
                    gear.price = Decimal(str(price))
                    gear.save(update_fields=["price"])
                updated += 1
                self.stdout.write(
                    f"  [{'SET' if apply else 'WOULD SET'}] "
                    f"{gear.type:12s} | {gear.brand:20s} | {gear.name:45s} | ${price:.2f}"
                )
            else:
                missing += 1
                missing_items.append(gear)
                self.stdout.write(
                    self.style.WARNING(
                        f"  [MISSING]   "
                        f"{gear.type:12s} | {gear.brand:20s} | {gear.name:45s} | NO PRICE FOUND"
                    )
                )

        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(f"  Results:")
        self.stdout.write(f"    Updated: {updated}/{total}")
        self.stdout.write(f"    Missing: {missing}/{total}")
        if not apply and updated > 0:
            self.stdout.write(
                self.style.WARNING(f"\n  ⚠ Dry-run mode. Run with --apply to save changes.")
            )
        if apply and updated > 0:
            self.stdout.write(self.style.SUCCESS(f"\n  ✅ Successfully updated {updated} prices!"))
        self.stdout.write(f"{'='*70}\n")

        if missing_items:
            self.stdout.write("\nItems without prices (need manual review):")
            for g in missing_items:
                self.stdout.write(f"  - [{g.type}] {g.brand} {g.name} (ID={g.gear_id})")

    def _get_price(self, gear):
        """
        Determine price for a gear item.
        Priority: 1) exact model override, 2) brand+category default
        """
        # 1. Try exact model name match
        if gear.name in MODEL_OVERRIDES:
            return MODEL_OVERRIDES[gear.name]

        # 2. Try brand + category default
        key = (gear.brand, gear.type)
        if key in BRAND_CATEGORY_DEFAULTS:
            return BRAND_CATEGORY_DEFAULTS[key]

        # 3. Fallback: try empty-brand defaults
        key_fallback = ("", gear.type)
        if key_fallback in BRAND_CATEGORY_DEFAULTS:
            return BRAND_CATEGORY_DEFAULTS[key_fallback]

        return None
