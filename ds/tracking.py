"""Optional MLflow experiment tracking.

No-ops if MLflow isn't installed (local DuckDB runs), so the models stay
runnable everywhere. On Databricks, MLflow is built in and runs are logged to
the workspace experiment automatically.
"""

from __future__ import annotations

import logging
from numbers import Number

log = logging.getLogger("ds.tracking")


def log_run(run_name: str, params: dict, metrics: dict, model=None) -> None:
    try:
        import mlflow
    except ImportError:
        log.info("mlflow not installed; skipping experiment tracking for %s.", run_name)
        return

    numeric = {k: v for k, v in metrics.items() if isinstance(v, Number)}
    with mlflow.start_run(run_name=run_name):
        mlflow.log_params(params)
        mlflow.log_metrics(numeric)
        if model is not None:
            try:
                import mlflow.sklearn

                mlflow.sklearn.log_model(model, "model")
            except Exception as exc:  # pragma: no cover - depends on flavor
                log.warning("Could not log model artifact: %s", exc)
    log.info("Logged MLflow run '%s' (%d metrics).", run_name, len(numeric))
