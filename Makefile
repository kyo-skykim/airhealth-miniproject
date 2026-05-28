.PHONY: help install ingest load dbt models run-local dashboard test lint clean

DBT_ENV = DBT_PROFILES_DIR=. DUCKDB_PATH=$(CURDIR)/data/warehouse.duckdb

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

ingest: ## Extract sources -> raw parquet zone
	python -m ingestion.run_ingest

load: ## Load raw parquet into the warehouse (DuckDB)
	python -m ingestion.load_warehouse

dbt: ## Run dbt build (transform + test)
	cd dbt && $(DBT_ENV) dbt build

models: ## Train DS models (forecast + regression)
	python -m ds.run_models

run-local: ingest load dbt models ## Full local pipeline end-to-end

dashboard: ## Launch the Streamlit dashboard
	streamlit run dashboard/app.py

test: ## Run unit tests
	pytest

lint: ## Lint with ruff
	ruff check .

clean: ## Remove data + warehouse artifacts
	rm -rf data dbt/target dbt/logs
