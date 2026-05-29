# Databricks notebook source
# MAGIC %md
# MAGIC # AirHealth · 03 — Train models
# MAGIC Trains the PM2.5 forecast + asthma regression on the Delta marts, logs to
# MAGIC MLflow, and writes predictions back to `airhealth.analytics.*`.
# MAGIC Run after `dbt build --target databricks`.

# COMMAND ----------
# MAGIC %pip install scikit-learn xgboost pydantic pydantic-settings
# COMMAND ----------
dbutils.library.restartPython()  # noqa: F821

# COMMAND ----------
import os

os.environ["BACKEND"] = "databricks"
os.environ["DBX_CATALOG"] = "airhealth"

# COMMAND ----------
from ds.run_models import main

main()  # MLflow runs are logged to the notebook's experiment automatically

# COMMAND ----------
display(spark.table("airhealth.analytics.mart_pm25_forecast"))  # noqa: F821
# COMMAND ----------
display(spark.table("airhealth.analytics.mart_asthma_predictions"))  # noqa: F821
