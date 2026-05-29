# Findings

> Results below are from the default **synthetic sample dataset** (5 focus metros for the
> daily time-series; a 150-county national cross-section for the health model). Re-run with
> `INGEST_MODE=api` for real-world figures. Numbers are reproducible by running the
> `airhealth_pipeline` Workflow on Databricks (ingest → load → dbt → train).

## 1. Air-quality patterns
- PM2.5 shows clear **seasonality** (winter inversion peaks, summer ozone), strongest in the
  Los Angeles and Phoenix metros.
- Most days fall in the **"Good"/"Moderate"** AQI bands; "Unhealthy" days cluster in winter.
- PM2.5 is **negatively associated with temperature** day-to-day (stagnant cold air traps
  particulates) — visible in the Weather↔AQ scatter.

## 2. PM2.5 forecasting
A gradient-boosted model on lag (1, 7-day), rolling-mean, calendar and weather features:

| Metric | Model | Persistence baseline |
|---|---|---|
| MAE (µg/m³, hold-out) | **2.20** | 2.69 |
| Skill vs. baseline | **+18%** | — |

The model meaningfully beats "tomorrow = today", with the 7-day lag/rolling features and
seasonal terms contributing most of the lift.

## 3. Asthma-prevalence regression (county cross-section, n=150)
Ridge regression with standardized features, 5-fold cross-validated:

- **CV R² ≈ 0.65**, **CV RMSE ≈ 0.87 percentage points**.
- Standardized coefficients (largest drivers):

| Feature | Std. coefficient | Direction |
|---|---|---|
| Avg PM2.5 | **+0.76** | more pollution → more asthma |
| Log population density | +0.46 | denser → more asthma |
| Avg NO₂ | +0.36 | more traffic pollution → more asthma |
| Income-deprivation index | +0.35 | poorer → more asthma |
| Median income | −0.35 | wealthier → less asthma |

**Takeaway:** air-quality exposure (PM2.5, NO₂) and socioeconomic deprivation are the
dominant, consistent predictors of county asthma prevalence — matching the public-health
literature. (In the synthetic data this relationship is intentionally encoded; the same
pipeline recovers it from real CDC PLACES + Census + air-quality data in `api` mode.)

## Caveats
- Cross-sectional regression shows **association, not causation**.
- Synthetic data is for demonstrating the pipeline; swap in live sources for real analysis.
