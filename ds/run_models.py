"""Run both DS models and emit a metrics summary (called by the Airflow DAG)."""

from __future__ import annotations

import json
import logging

from ds import forecast_pm25, regression_asthma

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ds.run")


def main() -> None:
    summary = {
        "pm25_forecast": forecast_pm25.run(),
        "asthma_regression": regression_asthma.run(),
    }
    log.info("DS model summary:\n%s", json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
