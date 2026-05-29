# Databricks notebook source
# MAGIC %md
# MAGIC # AirHealth · 00 — One-time setup (Unity Catalog)
# MAGIC Creates the catalog, schemas and the landing volume the pipeline writes to.
# MAGIC Run this once before the pipeline notebooks.

# COMMAND ----------

catalog = "airhealth"
raw_schema = "raw"
analytics_schema = "analytics"
volume = "landing"

# COMMAND ----------

spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")  # noqa: F821
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{raw_schema}")  # noqa: F821
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{analytics_schema}")  # noqa: F821
spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.{raw_schema}.{volume}")  # noqa: F821

print(f"Landing volume ready at: /Volumes/{catalog}/{raw_schema}/{volume}")
