"""
seed_data.py
------------
Management command to load the parquet file into the database.

Usage:
  python manage.py seed_data
  python manage.py seed_data --file /absolute/path/to/file.parquet
  python manage.py seed_data --batch-size 2000
"""

import logging
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.rates.services import ingestion_service

logger = logging.getLogger(__name__)


DEFAULT_FILE = Path(settings.BASE_DIR).parent / "data" / "rates_seed.parquet"


class Command(BaseCommand):
    help = "Seed the database from a parquet file (default: data/rates_seed.parquet)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=str(DEFAULT_FILE),
            help=f"Path to the parquet file (default: {DEFAULT_FILE})",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=5000,
            help="Number of records per bulk_create batch (default: 5000)",
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        batch_size = options["batch_size"]

        # --- Validate file ---
        if not os.path.exists(file_path):
            raise CommandError(
                f"Parquet file not found: {file_path}\n"
                "Place the file at data/rates_seed.parquet or pass --file <path>"
            )

        self.stdout.write(self.style.NOTICE(f"Loading: {file_path}"))
        self.stdout.write(self.style.NOTICE(f"Batch size: {batch_size}"))

        try:
            # loading data from parquet
            df = ingestion_service.load_parquet(file_path)
            self.stdout.write(f"  Rows loaded from parquet : {len(df):,}")

            # Cleaning data
            df = ingestion_service.clean_dataframe(df)
            self.stdout.write(f"  Rows after cleaning      : {len(df):,}")

            # Inserting data in batches
            result = ingestion_service.batch_insert(df, batch_size=batch_size)

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nDone! {result['total_processed']:,} rows processed "
                    f"across {result['batches']} batch(es).\n"
                    "Duplicates were silently skipped (ignore_conflicts=True)."
                )
            )

        except ValueError as exc:
            raise CommandError(f"Data error: {exc}") from exc
        except Exception as exc:
            logger.exception("Unexpected error during seed_data: %s", exc)
            raise CommandError(f"Unexpected error: {exc}") from exc
