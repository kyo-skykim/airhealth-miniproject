# Architecture & Data Dictionary

## Medallion architecture (Bronze → Silver → Gold)

The warehouse follows the medallion pattern on Databricks (Delta + Unity
Catalog). Each layer is a separate schema in the `airhealth` catalog:

```
ingestion/ ──> BRONZE ──dbt──> SILVER ──dbt──> GOLD ──> DS models + BI dashboard
 (extract)     (raw)          (clean)         (serve)        ▲   │
                                                             └── predictions
```

| Layer | Schema | Built by | Materialization | Contents |
|---|---|---|---|---|
| **Bronze** | `bronze` | `ingestion/` + `load_warehouse.py` | Delta tables | Raw ingested data, as-landed, pydantic-validated. One table per source. |
| **Silver** | `silver` | dbt (`models/silver/`) | views | Typed/cleaned (`stg_*`) and conformed/joined-to-grain (`int_*`). Plus the `metros` reference seed. |
| **Gold** | `gold` | dbt (`models/gold/`) + `ds/` | tables | Business-ready star schema (`dim_*`, `fact_*`), the county analytical mart, and the DS prediction tables. |

### Layer-by-layer

1. **Ingestion (`ingestion/`)** → **Bronze.** Each source has a `sample`/`api`
   extractor; records are pydantic-validated (`common/schemas.py`) and written as
   partitioned parquet (`common/io.py`) to the bronze UC volume. `load_warehouse.py`
   reads that parquet with Spark and writes the managed `bronze.*` Delta tables.

2. **Silver (`dbt/models/silver/`).** `stg_*` cast/clean each bronze source;
   `int_*` pivot pollutants and join air quality + weather onto the metro/day
   grain. Materialized as views — cheap, always fresh, not for direct BI use.

3. **Gold (`dbt/models/gold/`).** The serving layer: a star schema + analytical
   mart, materialized as tables. This is the **only layer DS and DA read from**.

4. **Data Science (`ds/`)** reads **gold**, trains models, and writes predictions
   **back into gold** (reverse-ELT), so model output sits next to the facts.

5. **Analysis (`dashboard/`)** reads **gold** only (Streamlit via the Databricks
   SQL connector; or a Databricks AI-BI dashboard on the same gold tables).

6. **Orchestration & CI** — a Databricks Workflow (`databricks.yml` Asset Bundle)
   chains the steps; GitHub Actions runs lint + tests + an ingestion smoke check.

## What DS and DA consume (the gold contract)

Both DS and DA depend **only on gold** — never on bronze/silver — so upstream
refactors don't break them as long as the gold contract holds.

| Gold table | Grain | Used by **DS** | Used by **DA** |
|---|---|---|---|
| `dim_date` | day | calendar features (join) | date filters / trend axis |
| `dim_location` | metro | join for metadata | maps, metro labels, demographics |
| `fact_air_quality_daily` | metro / day | **PM2.5 forecast** training features | trend lines, AQI mix, weather↔AQ |
| `mart_health_air_quality` | county | **asthma regression** training table | health-vs-pollution cross-section |
| `mart_pm25_forecast` *(DS output)* | metro / day | — | actual-vs-predicted charts |
| `mart_asthma_predictions` *(DS output)* | county | — | predicted-vs-actual scatter |

- **DS reads:** `fact_air_quality_daily` (time-series features) and
  `mart_health_air_quality` (cross-sectional features) → see `ds/warehouse.py`.
- **DS writes:** `mart_pm25_forecast`, `mart_asthma_predictions` (into gold).
- **DA reads:** every gold table above (`dashboard/app.py`).
- **Silver/bronze** are pipeline-internal; DS may dip into silver for ad-hoc
  feature engineering, but the supported, tested contract is gold.

## Gold star schema

| Model | Grain | Key columns |
|---|---|---|
| `dim_date` | 1 row / day | `date_day` (PK), `season`, `is_weekend`, `day_of_week` |
| `dim_location` | 1 row / metro | `metro_key` (PK), `county_fips`, `population`, `median_income`, `lat`, `lon` |
| `fact_air_quality_daily` | 1 row / metro / day | `air_quality_key` (PK), `metro_key` (FK), `observed_date` (FK), `pm25`, `pm10`, `no2`, `o3`, weather cols, `pm25_aqi_category` |
| `mart_health_air_quality` | 1 row / county | `county_fips` (PK), `avg_pm25`, `avg_no2`, `median_income`, `pop_density`, engineered features, `asthma_prevalence_pct`, `copd_prevalence_pct` |

### DS output tables (written back into gold by `ds/`)
| Table | Grain | Columns |
|---|---|---|
| `mart_pm25_forecast` | metro / day (hold-out) | `pm25_actual`, `pm25_predicted` |
| `mart_asthma_predictions` | county | `asthma_actual`, `asthma_predicted` (cross-validated) |

## Sources (land in bronze)

| Source | Live API | Grain |
|---|---|---|
| Air quality | OpenAQ v3 | daily, per metro |
| Weather | Open-Meteo archive | daily, per metro |
| Demographics | US Census ACS | per county |
| Health | CDC PLACES | per county |
| County cross-section | CDC PLACES + ACS + AQ summaries | per county (national sample) |
