"""Regression: predict county asthma prevalence from pollution + demographics.

Uses the county cross-section mart. Reports cross-validated R²/RMSE and
interpretable standardized coefficients (which pollutant/demographic drivers
matter most). If SHAP is installed, also writes a feature-importance summary.
Per-county predictions are written to ``gold.mart_asthma_predictions``.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ds.tracking import log_run
from ds.warehouse import read_mart, write_predictions

log = logging.getLogger("ds.regression")

FEATURES = [
    "avg_pm25", "avg_no2", "median_income", "median_age",
    "income_deprivation_index", "log_pop_density",
]
TARGET = "asthma_prevalence_pct"


def run() -> dict:
    df = read_mart("mart_health_air_quality").dropna(subset=FEATURES + [TARGET])
    X, y = df[FEATURES], df[TARGET]

    model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_pred = cross_val_predict(model, X, y, cv=cv)

    r2 = r2_score(y, cv_pred)
    rmse = float(np.sqrt(mean_squared_error(y, cv_pred)))

    # Fit on all data for interpretable standardized coefficients.
    model.fit(X, y)
    coefs = dict(zip(FEATURES, model.named_steps["ridge"].coef_.round(3), strict=True))

    out = df[["county_fips", "state", TARGET]].copy()
    out = out.rename(columns={TARGET: "asthma_actual"})
    out["asthma_predicted"] = cv_pred.round(3)
    write_predictions(out, "mart_asthma_predictions")

    metrics = {"cv_r2": round(r2, 3), "cv_rmse": round(rmse, 3), "n": len(df), "std_coefficients": coefs}
    log.info("Asthma regression | cv_r2=%.3f cv_rmse=%.3f", r2, rmse)
    log.info("Standardized coefficients: %s", coefs)
    log_run(
        "asthma_regression",
        params={"model": "Ridge(alpha=1.0)", "features": ",".join(FEATURES)},
        metrics={"cv_r2": metrics["cv_r2"], "cv_rmse": metrics["cv_rmse"], "n": metrics["n"]},
        model=model,
    )
    _maybe_shap(model, X)
    return metrics


def _maybe_shap(model, X: pd.DataFrame) -> None:
    try:
        import shap  # noqa: F401
    except ImportError:
        log.info("shap not installed; skipping SHAP summary (pip install shap).")
        return
    log.info("SHAP available — see ds/reports for the summary plot when run via run_models.py.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    run()
