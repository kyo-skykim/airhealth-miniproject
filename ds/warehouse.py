"""DS data-access layer: read GOLD marts, write predictions back to GOLD.

The science layer consumes the same gold Delta tables the BI layer does, so both
read one stable contract. Runs on Databricks (Spark / Unity Catalog).
"""

from __future__ import annotations

import pandas as pd

from ingestion.common.config import settings


def _spark():
    from pyspark.sql import SparkSession

    return SparkSession.builder.getOrCreate()


def _gold_table(name: str) -> str:
    return f"{settings.dbx_catalog}.{settings.dbx_gold_schema}.{name}"


def read_mart(name: str) -> pd.DataFrame:
    return _spark().table(_gold_table(name)).toPandas()


def write_predictions(df: pd.DataFrame, table: str = "mart_predictions") -> None:
    """Persist model output back into the GOLD schema (reverse-ELT)."""
    _spark().createDataFrame(df).write.mode("overwrite").option(
        "overwriteSchema", "true"
    ).saveAsTable(_gold_table(table))
