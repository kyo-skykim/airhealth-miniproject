# Running AirHealth on Databricks

AirHealth runs on Databricks with **Delta Lake + Unity Catalog** for the medallion
warehouse, **dbt-databricks** for transformations, **Databricks Workflows** for
orchestration and **MLflow** for model tracking.

## Medallion layers (Unity Catalog)

| Layer | Location | Built by |
|---|---|---|
| **Bronze** (raw) | parquet on the UC **Volume** `/Volumes/airhealth/bronze/landing` → Delta `airhealth.bronze.*` | `ingestion/` + `load_warehouse.py` (Spark) |
| **Silver** (clean) | Delta views `airhealth.silver.*` | dbt `models/silver/` |
| **Gold** (serve) | Delta tables `airhealth.gold.*` | dbt `models/gold/` + `ds/` |
| Tracking | MLflow (automatic) | `ds/` |

dbt cross-database type macros (`dbt.type_string()`, `dbt.type_float()`, …) keep
the SQL clean and portable across Spark.

## Option A — Notebooks (interactive, simplest)

1. Add this repo to your workspace as a **Git folder** (Repos), so the
   `ingestion` / `ds` packages are importable from notebooks.
2. Run `databricks/notebooks/00_setup.py` once (creates catalog, schemas, volume).
3. Run `01_ingest` → `02_load_warehouse`, then `dbt build --target databricks`
   (a dbt task or `%sh cd dbt && dbt build --target databricks`), then
   `03_train_models`.

## Option B — Asset Bundle (Workflow Job, deployable)

```bash
pip install databricks-cli            # or use the new `databricks` CLI
databricks bundle validate
databricks bundle deploy -t dev
databricks bundle run airhealth_pipeline -t dev
```

`databricks.yml` defines the `airhealth_pipeline` job: **ingest → load → dbt_build
→ train_models**. Set the `warehouse_id` variable to a SQL warehouse and adjust
`node_type_id` / `spark_version` for your cloud (AWS/Azure/GCP).

## Dashboard

Build a **Databricks AI/BI dashboard** (or Databricks SQL dashboard) directly on
`airhealth.gold.*` — the same gold tables the Streamlit app uses. Suggested tiles
mirror the Streamlit tabs: daily PM2.5 trend, AQI category mix, weather↔AQ scatter,
county asthma-vs-PM2.5 cross-section, and the `mart_pm25_forecast` /
`mart_asthma_predictions` model-result charts. The Streamlit app can also be hosted
via **Databricks Apps** if you prefer to keep it.

## Notes
- Requires Unity Catalog + a cluster/warehouse with permission to create the
  catalog/schemas/volume (or have an admin pre-create them).
- The ingestion sample mode needs no network; for live data set `INGEST_MODE=api`
  and provide API keys as cluster env vars / secrets.
