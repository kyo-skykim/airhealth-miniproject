# Databricks notebook source
# MAGIC %md
# MAGIC # AirHealth · 01 — Ingest
# MAGIC Extracts the sources (synthetic by default) and writes validated parquet to
# MAGIC the Unity Catalog landing volume. Reuses `ingestion.run_ingest` unchanged.

# COMMAND ----------
# MAGIC %pip install pydantic pydantic-settings pyarrow
# COMMAND ----------
dbutils.library.restartPython()  # noqa: F821

# COMMAND ----------
import os

# The repo (added as a Git folder or synced by the Asset Bundle) is importable
# via Databricks "files in workspace". Configure the databricks backend:
os.environ["BACKEND"] = "databricks"
os.environ["INGEST_MODE"] = "sample"          # set "api" + keys for live data
os.environ["DATA_DIR"] = "/Volumes/airhealth/raw/landing"
os.environ["DBX_CATALOG"] = "airhealth"

# COMMAND ----------
from ingestion.run_ingest import main

main()

# COMMAND ----------
# MAGIC %md Raw parquet now under `/Volumes/airhealth/raw/landing/raw/<source>/`.
