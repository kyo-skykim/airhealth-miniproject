"""IO layer: write validated records as partitioned parquet to the landing zone.

Writes under ``DATA_DIR`` — a local path for dev/CI, or the bronze Unity Catalog
volume (e.g. /Volumes/airhealth/bronze/landing) on Databricks. ``load_warehouse``
then exposes these as the bronze Delta tables.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel

from ingestion.common.config import settings

log = logging.getLogger(__name__)


def _records_to_table(records: list[BaseModel]) -> pa.Table:
    rows = [r.model_dump(mode="json") for r in records]
    return pa.Table.from_pandas(pd.DataFrame(rows), preserve_index=False)


def write_records(source: str, partition: str, records: list[BaseModel]) -> str:
    """Write validated records as parquet for one partition. Returns the path/URI."""
    if not records:
        log.warning("No records for source=%s partition=%s; skipping write.", source, partition)
        return ""

    table = _records_to_table(records)

    path: Path = settings.raw_path(source, partition)
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)
    log.info("Wrote %d records -> %s", len(records), path)
    return str(path)
