"""DS data-access layer: read marts from the warehouse, write predictions back.

Reads through the same marts dbt produces, so the science layer consumes the
exact contract the analytics layer does. DuckDB by default; the BigQuery path is
documented for the cloud backend.
"""

from __future__ import annotations

import pandas as pd

from ingestion.common.config import settings


def _connect():
    if settings.backend == "bigquery":  # pragma: no cover - needs cloud creds
        raise SystemExit(
            "Reading marts from BigQuery: use google-cloud-bigquery / pandas-gbq with "
            f"project={settings.gcp_project!r}, dataset={settings.bq_dataset_analytics!r}."
        )
    import duckdb

    return duckdb.connect(str(settings.duckdb_path))


def read_mart(name: str) -> pd.DataFrame:
    con = _connect()
    try:
        return con.execute(f"SELECT * FROM analytics.{name}").df()
    finally:
        con.close()


def write_predictions(df: pd.DataFrame, table: str = "mart_predictions") -> None:
    """Persist model output back into the analytics schema (reverse-ELT)."""
    con = _connect()
    try:
        con.register("_preds", df)
        con.execute(f"CREATE OR REPLACE TABLE analytics.{table} AS SELECT * FROM _preds")
    finally:
        con.close()
