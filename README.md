# 🌬️ AirHealth — Air Quality & Respiratory Health Analytics Platform

An end-to-end **Data Engineering → Data Science → Data Analysis** portfolio project.
It links **air quality + weather + demographics** to **respiratory-health outcomes**
across US metros, demonstrating a full modern-data-stack pipeline.

> **Runs anywhere with one command** — defaults to offline synthetic data + a local
> DuckDB warehouse, so reviewers need **no cloud account and no API keys**. The same
> code targets **GCP (BigQuery + GCS + Cloud Composer)** by flipping two env vars.

## What this demonstrates

| Discipline | In this project |
|---|---|
| **Data Engineering** | Multi-source ingestion w/ retries + schema validation, partitioned parquet raw zone, DuckDB/BigQuery warehouse, **dbt** star schema + tests + docs, **Airflow** orchestration, **Terraform** IaC, Docker, GitHub Actions CI |
| **Data Science** | PM2.5 time-series forecasting (gradient boosting vs. persistence baseline), county asthma-prevalence regression (cross-validated, interpretable coefficients), predictions written back to the warehouse |
| **Data Analysis** | Streamlit dashboard (trends, AQI mix, weather↔AQ, health cross-section, model results), a written findings narrative, and a Looker Studio recipe for the cloud backend |

## Architecture

```mermaid
flowchart LR
    A[Public APIs / sample] -->|Python extractors + pydantic| B[Raw zone: partitioned parquet]
    B -->|load| C[(Warehouse: DuckDB / BigQuery)]
    C -->|dbt staging→intermediate→marts| D[Star-schema marts]
    D --> E[DS: forecast + regression]
    E -->|predictions| C
    D --> F[Streamlit / Looker Studio]
    G[Airflow] -. orchestrates .-> A & B & C & E
```

See [`docs/architecture.md`](docs/architecture.md) for the data dictionary and layer-by-layer detail.

## Quickstart (local, ~1 minute)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

make run-local      # ingest → load → dbt build (+ tests) → train models
make dashboard      # open http://localhost:8501
```

Or with Docker:

```bash
docker compose -f docker/docker-compose.yml up pipeline   # pipeline + dashboard on :8501
docker compose -f docker/docker-compose.yml up airflow    # Airflow UI on :8080
```

## Going to the cloud (GCP)

```bash
cd infra/terraform && terraform init && terraform apply -var project_id=YOUR_PROJECT
# then in .env: BACKEND=bigquery, set GCP_PROJECT / GCS_BUCKET / GOOGLE_APPLICATION_CREDENTIALS
pip install dbt-bigquery
make run-local      # same commands, now targeting BigQuery
# build the Looker Studio report on the analytics dataset (see docs/architecture.md)
```

## Live data instead of synthetic

Set `INGEST_MODE=api` (and provide `OPENAQ_API_KEY` / `CENSUS_API_KEY`) to pull from
[OpenAQ](https://openaq.org), [Open-Meteo](https://open-meteo.com),
[CDC PLACES](https://www.cdc.gov/places/) and the [Census ACS](https://www.census.gov/data/developers.html).

## Repo layout

```
ingestion/      extractors + shared http/io/schema/sample layer + warehouse loader
dbt/            sources, staging, intermediate, marts, tests, macros, seeds
ds/             forecasting + regression models, warehouse access, runner
dashboard/      Streamlit app
orchestration/  Airflow DAG
infra/          Terraform (GCS + BigQuery, optional Composer)
docker/         Dockerfile + docker-compose (pipeline + Airflow)
docs/           architecture + data dictionary + findings
tests/          unit tests
```

## Results (sample data)

- **PM2.5 forecast**: beats the persistence baseline (~18% MAE reduction on hold-out).
- **Asthma regression**: cross-validated R² ≈ 0.65; PM2.5 and income-deprivation are the
  strongest drivers — see [`docs/findings.md`](docs/findings.md).
