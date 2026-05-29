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


def load_databricks() -> None:  # pragma: no cover - runs on a Databricks cluster
    """Read the raw parquet zone with Spark and write managed Delta tables.

    Creates ``<catalog>.<raw_schema>.<source>`` Delta tables that the
    dbt-databricks sources read. Run on a cluster where ``DATA_DIR`` points at
    the Unity Catalog volume the ingestion wrote to
    (e.g. /Volumes/airhealth/raw/landing).
    """
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()
    cat, schema = settings.dbx_catalog, settings.dbx_raw_schema
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {cat}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {cat}.{schema}")
    for source in SOURCES:
        src_dir = (settings.raw_dir / source).resolve().as_posix()
        df = spark.read.option("recursiveFileLookup", "true").parquet(src_dir)
        table = f"{cat}.{schema}.{source}"
        df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(table)
        log.info("%s -> %d rows", table, df.count())


def main() -> None:
    if settings.backend == "bigquery":
        load_bigquery()
    elif settings.backend == "databricks":
        load_databricks()
    else:
        load_duckdb()


if __name__ == "__main__":
    main()
