# Databricks notebook source
# MAGIC %md
# MAGIC # AirHealth · 00 — One-time setup (Unity Catalog)
# MAGIC Creates the catalog, schemas and the landing volume the pipeline writes to.
# MAGIC Run this once before the pipeline notebooks.

# COMMAND ----------

catalog = "airhealth"
volume = "landing"

# COMMAND ----------
# Medallion schemas: bronze (raw), silver (cleaned), gold (DS/DA consumption)
spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")  # noqa: F821
for schema in ("bronze", "silver", "gold"):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")  # noqa: F821
spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.bronze.{volume}")  # noqa: F821

print(f"Bronze landing volume ready at: /Volumes/{catalog}/bronze/{volume}")
