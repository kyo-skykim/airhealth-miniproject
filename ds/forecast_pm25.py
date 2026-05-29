"""Time-series model: forecast daily PM2.5 per metro from the daily fact.

Builds lag + calendar + weather features and trains a gradient-boosted model,
evaluated against a persistence (yesterday's value) baseline on a temporal
hold-out. Predictions are written back to ``analytics.mart_pm25_forecast``.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

from ds.tracking import log_run
from ds.warehouse import read_mart, write_predictions

log = logging.getLogger("ds.forecast")

FEATURES = [
    "pm25_lag1", "pm25_lag7", "pm25_roll7",
    "temp_c", "humidity_pct", "wind_kph", "precip_mm",
    "doy_sin", "doy_cos", "dow",
]


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["metro_key", "observed_date"]).copy()
    g = df.groupby("metro_key", group_keys=False)
    df["pm25_lag1"] = g["pm25"].shift(1)
    df["pm25_lag7"] = g["pm25"].shift(7)
    df["pm25_roll7"] = g["pm25"].shift(1).rolling(7).mean().reset_index(level=0, drop=True)
    doy = df["observed_date"].dt.dayofyear
    df["doy_sin"] = np.sin(2 * np.pi * doy / 365)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 365)
    df["dow"] = df["observed_date"].dt.dayofweek
    return df.dropna(subset=FEATURES + ["pm25"])


def run() -> dict:
    fact = read_mart("fact_air_quality_daily")
    fact["observed_date"] = pd.to_datetime(fact["observed_date"])
    feat = _build_features(fact)

    # Temporal split: last 20% of days held out.
    cutoff = feat["observed_date"].quantile(0.8)
    train = feat[feat["observed_date"] <= cutoff]
    test = feat[feat["observed_date"] > cutoff]

    model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_depth=4, random_state=42)
    model.fit(train[FEATURES], train["pm25"])
    preds = model.predict(test[FEATURES])

    model_mae = mean_absolute_error(test["pm25"], preds)
    baseline_mae = mean_absolute_error(test["pm25"], test["pm25_lag1"])  # persistence
    skill = 1 - model_mae / baseline_mae

    out = test[["metro_key", "observed_date", "pm25"]].copy()
    out = out.rename(columns={"pm25": "pm25_actual"})
    out["pm25_predicted"] = preds
    write_predictions(out, "mart_pm25_forecast")

    metrics = {
        "model_mae": round(model_mae, 3),
        "baseline_mae": round(baseline_mae, 3),
        "skill_vs_baseline": round(skill, 3),
        "n_train": len(train),
        "n_test": len(test),
    }
    log.info("PM2.5 forecast | %s", metrics)
    if skill <= 0:
        log.warning("Model did not beat the persistence baseline (skill=%.3f).", skill)
    log_run(
        "pm25_forecast",
        params={"model": "HistGradientBoostingRegressor", "features": ",".join(FEATURES)},
        metrics=metrics,
        model=model,
    )
    return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    run()
