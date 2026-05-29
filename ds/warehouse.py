"""DS data-access layer: read GOLD marts, write predictions back to GOLD.

The science layer consumes the same gold tables the analytics/BI layer does, so
both read one stable contract. Backend-aware:
  * duckdb     (default) — local DuckDB file
  * databricks — Spark / Unity Catalog Delta tables (runs on a cluster)
  * bigquery   — documented path (use google-cloud-bigquery / pandas-gbq)
"""

from __future__ import annotations

import pandas as pd

from ingestion.common.config import settings


def _dbx_table(name: str) -> str:
    return f"{settings.dbx_catalog}.{settings.dbx_gold_schema}.{name}"


def read_mart(name: str) -> pd.DataFrame:
    if settings.backend == "databricks":  # pragma: no cover - runs on a cluster
        from pyspark.sql import SparkSession

        spark = SparkSession.builder.getOrCreate()
        return spark.table(_dbx_table(name)).toPandas()

    if settings.backend == "bigquery":  # pragma: no cover - needs cloud creds
        raise SystemExit(
            "Reading gold marts from BigQuery: use google-cloud-bigquery / pandas-gbq with "
            f"project={settings.gcp_project!r}, dataset={settings.bq_dataset_analytics!r}."
        )

    import duckdb

    con = duckdb.connect(str(settings.duckdb_path))
    try:
        return con.execute(f"SELECT * FROM gold.{name}").df()
    finally:
        con.close()


def write_predictions(df: pd.DataFrame, table: str = "mart_predictions") -> None:
    """Persist model output back into the GOLD schema (reverse-ELT)."""
    if settings.backend == "databricks":  # pragma: no cover - runs on a cluster
        from pyspark.sql import SparkSession

        spark = SparkSession.builder.getOrCreate()
        spark.createDataFrame(df).write.mode("overwrite").option(
            "overwriteSchema", "true"
        ).saveAsTable(_dbx_table(table))
        return

    import duckdb

    con = duckdb.connect(str(settings.duckdb_path))
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS gold")
        con.register("_preds", df)
        con.execute(f"CREATE OR REPLACE TABLE gold.{table} AS SELECT * FROM _preds")
    finally:
        con.close()
