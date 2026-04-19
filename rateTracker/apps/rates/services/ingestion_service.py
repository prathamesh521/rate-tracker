"""
ingestion_service.py
--------------------
Handles all data-ingestion logic:
  - Reading parquet files with pandas + pyarrow
  - Cleaning / normalising the DataFrame
  - Batch-inserting into the database

Kept separate from views so it can be called from both the management
command (seed_data) and the POST /rates/ingest API endpoint.
"""

import logging
from datetime import date

import pandas as pd
from django.db import transaction

from apps.rates.models import Rate

logger = logging.getLogger(__name__)

# Columns that MUST be present in the parquet file
REQUIRED_COLUMNS = {"provider_name", "rate_type", "rate_value", "effective_date"}


# ---------------------------------------------------------------------------
# Parquet helpers
# ---------------------------------------------------------------------------

def load_parquet(file_path: str) -> pd.DataFrame:
    """Read a parquet file and return a DataFrame."""
    logger.info("Loading parquet file: %s", file_path)
    df = pd.read_parquet(file_path, engine="pyarrow")
    logger.info("Loaded %d rows from parquet", len(df))
    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if "provider" in df.columns and "provider_name" not in df.columns:
        df = df.rename(columns={"provider": "provider_name"})

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Parquet file is missing required columns: {missing}")

    original_count = len(df)

    # --- Drop nulls in required columns ---
    df = df.dropna(subset=list(REQUIRED_COLUMNS))

    # --- Trim string columns ---
    df["provider_name"] = df["provider_name"].astype(str).str.strip()
    df["rate_type"] = df["rate_type"].astype(str).str.strip()

    # --- Coerce numeric ---
    df["rate_value"] = pd.to_numeric(df["rate_value"], errors="coerce")

    # --- Coerce date ---
    df["effective_date"] = pd.to_datetime(df["effective_date"], errors="coerce").dt.date

    # --- Drop rows that failed coercion ---
    df = df.dropna(subset=["rate_value", "effective_date"])

    # --- Remove empty strings after strip ---
    df = df[df["provider_name"].str.len() > 0]
    df = df[df["rate_type"].str.len() > 0]

    dropped = original_count - len(df)
    if dropped:
        logger.warning("Dropped %d invalid/null rows during cleaning", dropped)

    logger.info("Clean DataFrame: %d rows ready for insert", len(df))
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Batch insert
# ---------------------------------------------------------------------------

def batch_insert(df: pd.DataFrame, batch_size: int = 5000) -> dict:
    total = len(df)
    if total == 0:
        logger.warning("batch_insert called with an empty DataFrame — nothing to insert.")
        return {"total_processed": 0, "batches": 0}

    batch_count = 0

    for start in range(0, total, batch_size):
        chunk = df.iloc[start : start + batch_size]
        objects = [
            Rate(
                provider_name=row.provider_name,
                rate_type=row.rate_type,
                rate_value=float(row.rate_value),
                effective_date=row.effective_date,
            )
            for row in chunk.itertuples(index=False)
        ]

       
        Rate.objects.bulk_create(objects, ignore_conflicts=True)

        batch_count += 1
        processed_so_far = min(start + batch_size, total)
        logger.info("Batch %d complete — %d / %d rows processed", batch_count, processed_so_far, total)

    return {"total_processed": total, "batches": batch_count}


# ---------------------------------------------------------------------------
# Single-record upsert (used by POST /rates/ingest)
# ---------------------------------------------------------------------------

def save_single_rate(data: dict) -> tuple[Rate, bool]:
    rate, created = Rate.objects.update_or_create(
        provider_name=data["provider_name"],
        rate_type=data["rate_type"],
        effective_date=data["effective_date"],
        defaults={"rate_value": data["rate_value"]},
    )
    action = "Created" if created else "Updated"
    logger.info(
        "%s rate: %s | %s | %s = %.4f",
        action, rate.provider_name, rate.rate_type, rate.effective_date, rate.rate_value,
    )
    return rate, created
