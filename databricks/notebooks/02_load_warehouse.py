# Databricks notebook source
# MAGIC %md
# MAGIC # AirHealth · 02 — Load warehouse (Delta)
# MAGIC Reads the landing parquet with Spark and writes managed Delta tables into
# MAGIC `airhealth.bronze.*` (Unity Catalog). Reuses `ingestion.load_warehouse`.

# COMMAND ----------
# MAGIC %pip install pydantic pydantic-settings
# COMMAND ----------
dbutils.library.restartPython()  # noqa: F821

# COMMAND ----------
import os

os.environ["BACKEND"] = "databricks"
os.environ["DATA_DIR"] = "/Volumes/airhealth/bronze/landing"
os.environ["DBX_CATALOG"] = "airhealth"

# COMMAND ----------
from ingestion.load_warehouse import main

main()

# COMMAND ----------
display(spark.sql("SHOW TABLES IN airhealth.bronze"))  # noqa: F821
