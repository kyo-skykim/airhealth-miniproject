# Running AirHealth on Databricks

The same pipeline runs on Databricks with **Delta Lake + Unity Catalog** for the
warehouse, **dbt-databricks** for transformations, **Databricks Workflows** for
orchestration (replacing Airflow) and **MLflow** for model tracking. Flip the
backend with `BACKEND=databricks` — no application code changes.

## How the backend maps

| Medallion layer | Local (DuckDB) | Databricks |
|---|---|---|
| **Bronze** (raw) | parquet `./data/raw` → `bronze` views | parquet on a UC **Volume** (`/Volumes/airhealth/bronze/landing`) → Delta `airhealth.bronze.*` |
| **Silver** (clean) | `silver` schema views | Delta views/tables `airhealth.silver.*` |
| **Gold** (serve) | `gold` schema tables | Delta tables `airhealth.gold.*` |
| Transform | `dbt --target duckdb` | `dbt --target databricks` (SQL warehouse) |
| DS read/write (gold) | DuckDB | `spark.table(...)` / `saveAsTable(...)` |
| Orchestration | Airflow DAG | Workflow Job (`databricks.yml`) |
| Tracking | none | MLflow (automatic) |

Portability is handled by dbt cross-database type macros (`dbt.type_string()`,
`dbt.type_float()`, …) and `target.type` branching in `dim_date.sql`, so the same
models compile on DuckDB, BigQuery and Spark.

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
