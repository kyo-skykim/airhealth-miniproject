"""Central configuration, loaded from environment / .env.

A single `settings` object is reused across every extractor, the loader, the dbt
invocation and the DS scripts so behaviour is consistent and the `BACKEND` /
`INGEST_MODE` toggles flip the entire pipeline at once.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Backends / modes
    backend: str = Field(default="duckdb")  # duckdb | bigquery | databricks
    ingest_mode: str = Field(default="sample")  # sample | api

    # Local paths
    data_dir: Path = Field(default=Path("./data"))
    duckdb_path: Path = Field(default=Path("./data/warehouse.duckdb"))

    # Scope
    metros: str = Field(default="los_angeles,new_york,chicago,houston,phoenix")
    start_date: date = Field(default=date(2023, 1, 1))
    end_date: date = Field(default=date(2023, 12, 31))

    # API keys
    openaq_api_key: str = Field(default="")
    census_api_key: str = Field(default="")

    # Cloud (GCP / BigQuery)
    gcp_project: str = Field(default="")
    gcs_bucket: str = Field(default="")
    bq_dataset_raw: str = Field(default="airhealth_raw")
    bq_dataset_analytics: str = Field(default="airhealth_analytics")
    bq_location: str = Field(default="US")

    # Databricks (Unity Catalog + Delta)
    dbx_catalog: str = Field(default="airhealth")
    dbx_raw_schema: str = Field(default="raw")
    dbx_analytics_schema: str = Field(default="analytics")
    dbx_volume: str = Field(default="landing")  # UC volume for the raw parquet zone

    @property
    def metro_keys(self) -> list[str]:
        return [m.strip() for m in self.metros.split(",") if m.strip()]

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    def raw_path(self, source: str, partition: str) -> Path:
        """Partitioned parquet path, e.g. data/raw/openaq/dt=2023-01-01/data.parquet."""
        return self.raw_dir / source / f"dt={partition}" / "data.parquet"


settings = Settings()
