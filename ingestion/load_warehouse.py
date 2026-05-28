"""Load the raw parquet zone into the warehouse's raw schema.

DuckDB backend (default): creates a ``raw`` schema of views over the partitioned
parquet files, so dbt sources read fresh data with no copy step. The BigQuery
path documents the equivalent ``bq load`` into the raw dataset (run when
BACKEND=bigquery and GCP creds are present).
"""

from __future__ import annotations

import logging

import duckdb

from ingestion.common.config import settings

log = logging.getLogger("load")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

SOURCES = ("air_quality", "weather", "demographics", "health", "county_annual")


def load_duckdb() -> None:
    settings.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(settings.duckdb_path))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    for source in SOURCES:
        # Absolute path so the view resolves regardless of the caller's cwd
        # (e.g. dbt runs from the dbt/ directory).
        glob = (settings.raw_dir / source).resolve().as_posix() + "/**/*.parquet"
        con.execute(
            f"CREATE OR REPLACE VIEW raw.{source} AS "
            f"SELECT * FROM read_parquet('{glob}', union_by_name=true)"
        )
        n = con.execute(f"SELECT count(*) FROM raw.{source}").fetchone()[0]
        log.info("raw.%s -> %d rows", source, n)
    con.close()


def load_bigquery() -> None:  # pragma: no cover - requires cloud creds
    raise SystemExit(
        "BigQuery load: run `bq load --source_format=PARQUET "
        f"{settings.bq_dataset_raw}.<source> gs://{settings.gcs_bucket}/raw/<source>/*` "
        "for each source, or use the Airflow GCSToBigQueryOperator in "
        "orchestration/airflow/dags/airhealth_pipeline.py."
    )


def main() -> None:
    if settings.backend == "bigquery":
        load_bigquery()
    else:
        load_duckdb()


if __name__ == "__main__":
    main()
