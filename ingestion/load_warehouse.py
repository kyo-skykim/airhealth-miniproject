"""Load the parquet landing zone into the BRONZE Delta schema (Databricks).

Bronze is the first medallion layer: raw ingested data, as-landed. This reads
the partitioned parquet the ingestion wrote (to a Unity Catalog volume) with
Spark and writes managed Delta tables into ``<catalog>.bronze.*`` that the
dbt-databricks bronze sources read. Runs on a Databricks cluster.
"""

from __future__ import annotations

import logging

from ingestion.common.config import settings

log = logging.getLogger("load")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

SOURCES = ("air_quality", "weather", "demographics", "health", "county_annual")


def load_databricks() -> None:  # pragma: no cover - runs on a Databricks cluster
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()
    cat, schema = settings.dbx_catalog, settings.dbx_bronze_schema
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {cat}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {cat}.{schema}")
    for source in SOURCES:
        src_dir = (settings.raw_dir / source).resolve().as_posix()
        df = spark.read.option("recursiveFileLookup", "true").parquet(src_dir)
        table = f"{cat}.{schema}.{source}"
        df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(table)
        log.info("%s -> %d rows", table, df.count())


def main() -> None:
    load_databricks()


if __name__ == "__main__":
    main()
