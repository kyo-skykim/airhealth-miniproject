"""AirHealth end-to-end orchestration DAG.

ingest -> load warehouse -> dbt build (transform + test) -> train DS models.

Runs against the local DuckDB stack out of the box (docker-compose). For the
cloud backend, set BACKEND=bigquery + GCP creds in the Airflow environment and
the same tasks target BigQuery; the GCS->BigQuery load step is shown commented
below using GCSToBigQueryOperator.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"

default_args = {
    "owner": "airhealth",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="airhealth_pipeline",
    description="Ingest air quality/weather/health, transform with dbt, train models.",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["airhealth", "de", "ds"],
) as dag:
    ingest = BashOperator(
        task_id="ingest",
        bash_command=f"cd {PROJECT_DIR} && python -m ingestion.run_ingest",
    )

    load = BashOperator(
        task_id="load_warehouse",
        bash_command=f"cd {PROJECT_DIR} && python -m ingestion.load_warehouse",
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            f"cd {PROJECT_DIR}/dbt && DBT_PROFILES_DIR=. "
            f"DUCKDB_PATH={PROJECT_DIR}/data/warehouse.duckdb dbt build"
        ),
    )

    train = BashOperator(
        task_id="train_models",
        bash_command=f"cd {PROJECT_DIR} && python -m ds.run_models",
    )

    # Cloud variant (BACKEND=bigquery): replace `load_warehouse` with
    # GCSToBigQueryOperator tasks, e.g.
    #   from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
    #   load = GCSToBigQueryOperator(task_id="load_aq", bucket=..., source_objects=["raw/air_quality/*"],
    #       destination_project_dataset_table="airhealth_raw.air_quality", source_format="PARQUET")

    ingest >> load >> dbt_build >> train
