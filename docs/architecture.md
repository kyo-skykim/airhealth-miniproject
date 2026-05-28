# Architecture & Data Dictionary

## Layers

1. **Ingestion (`ingestion/`)** — Each source has an extractor with a `sample` and an
   `api` path. Records are validated with pydantic (`common/schemas.py`) and written as
   partitioned parquet to the raw zone (`common/io.py`): time-series sources are
   partitioned by month, static sources use a single partition. A single config object
   (`common/config.py`) drives the `BACKEND` and `INGEST_MODE` toggles for the whole stack.

2. **Warehouse load (`ingestion/load_warehouse.py`)** — DuckDB: creates a `raw` schema of
   views over the parquet (no copy). BigQuery: `bq load` / `GCSToBigQueryOperator`.

3. **Transformation (`dbt/`)** — `staging` (typed/cleaned views) → `intermediate`
   (pivot + join to the metro/day grain) → `marts` (star schema, materialized tables).
   Generic + relationship tests enforce the contract. `dbt docs generate` builds lineage.

4. **Data Science (`ds/`)** — Reads marts, trains models, writes predictions back into
   the `analytics` schema (reverse-ELT) so the dashboard shows model output alongside facts.

5. **Analysis (`dashboard/`)** — Streamlit reads the marts + prediction tables. For the
   cloud backend, build a Looker Studio report directly on the BigQuery `analytics` dataset.

6. **Orchestration & infra** — Airflow DAG chains the steps; Terraform provisions GCS +
   BigQuery (+ optional Composer); Docker + GitHub Actions make it reproducible.

## Star schema (marts)

| Model | Grain | Key columns |
|---|---|---|
| `dim_date` | 1 row / day | `date_day` (PK), `season`, `is_weekend`, `day_of_week` |
| `dim_location` | 1 row / metro | `metro_key` (PK), `county_fips`, `population`, `median_income`, `lat`, `lon` |
| `fact_air_quality_daily` | 1 row / metro / day | `air_quality_key` (PK), `metro_key` (FK), `observed_date` (FK), `pm25`, `pm10`, `no2`, `o3`, weather cols, `pm25_aqi_category` |
| `mart_health_air_quality` | 1 row / county | `county_fips` (PK), `avg_pm25`, `avg_no2`, `median_income`, `pop_density`, engineered features, `asthma_prevalence_pct`, `copd_prevalence_pct` |

### DS output tables (written back by `ds/`)
| Table | Grain | Columns |
|---|---|---|
| `mart_pm25_forecast` | metro / day (hold-out) | `pm25_actual`, `pm25_predicted` |
| `mart_asthma_predictions` | county | `asthma_actual`, `asthma_predicted` (cross-validated) |

## Sources

| Source | Live API | Grain |
|---|---|---|
| Air quality | OpenAQ v3 | daily, per metro |
| Weather | Open-Meteo archive | daily, per metro |
| Demographics | US Census ACS | per county |
| Health | CDC PLACES | per county |
| County cross-section | CDC PLACES + ACS + AQ summaries | per county (national sample) |
