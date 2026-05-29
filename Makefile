.PHONY: help install ingest lint test bundle-validate deploy run dashboard clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

ingest: ## Extract sources -> parquet landing zone (sample mode, no cluster needed)
	python -m ingestion.run_ingest

lint: ## Lint with ruff
	ruff check .

test: ## Run unit tests
	pytest

bundle-validate: ## Validate the Databricks Asset Bundle
	databricks bundle validate

deploy: ## Deploy the airhealth_pipeline Workflow to Databricks
	databricks bundle deploy -t dev

run: ## Run the airhealth_pipeline Workflow on Databricks
	databricks bundle run airhealth_pipeline -t dev

dashboard: ## Launch the Streamlit dashboard (connects to Databricks SQL)
	streamlit run dashboard/app.py

clean: ## Remove local parquet + dbt artifacts
	rm -rf data dbt/target dbt/logs
