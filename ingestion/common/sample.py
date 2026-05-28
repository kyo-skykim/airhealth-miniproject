"""Synthetic data generators (INGEST_MODE=sample, the default).

These produce realistic, deterministic data so the entire pipeline runs offline
with no API keys — important for CI, reviewers, and reproducibility. The data is
intentionally given structure (seasonality, weather/air-quality coupling, and a
demographics+pollution -> asthma relationship) so the downstream DS models learn
genuine signal rather than noise.
"""

from __future__ import annotations

import math
import random
from datetime import date, timedelta

from ingestion.common.locations import Metro
from ingestion.common.schemas import (
    AirQualityRecord,
    CountyAnnualRecord,
    DemographicsRecord,
    HealthRecord,
    WeatherRecord,
)

_STATES = ["CA", "NY", "IL", "TX", "AZ", "PA", "OH", "GA", "NC", "MI", "WA", "CO", "FL", "MA"]

# Per-metro baselines that drive the synthetic relationships.
_METRO_PROFILE = {
    # key: (base_pm25, base_temp_c, base_income, base_pop, base_age)
    "los_angeles": (18.0, 19.0, 71000, 10000000, 36.5),
    "new_york": (12.0, 13.0, 70000, 1600000, 37.0),
    "chicago": (11.0, 10.0, 65000, 5150000, 35.5),
    "houston": (13.5, 21.0, 60000, 4700000, 33.5),
    "phoenix": (15.0, 24.0, 62000, 4400000, 34.0),
}


def _seed_for(metro_key: str, salt: str) -> random.Random:
    return random.Random(f"{metro_key}:{salt}")


def _daterange(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def gen_air_quality(metro: Metro, start: date, end: date) -> list[AirQualityRecord]:
    base_pm25, base_temp, *_ = _METRO_PROFILE[metro.key]
    rng = _seed_for(metro.key, "aq")
    out: list[AirQualityRecord] = []
    for d in _daterange(start, end):
        doy = d.timetuple().tm_yday
        # Winter inversion + summer ozone style seasonality.
        season = 1.0 + 0.35 * math.cos(2 * math.pi * (doy - 15) / 365)
        pm25 = max(1.0, base_pm25 * season + rng.gauss(0, 2.5))
        pm10 = pm25 * (1.6 + rng.uniform(-0.1, 0.1))
        no2 = max(1.0, 14 * season + rng.gauss(0, 3))
        o3 = max(1.0, 30 + 18 * math.sin(2 * math.pi * (doy - 100) / 365) + rng.gauss(0, 4))
        for param, value, unit in (
            ("pm25", pm25, "ug/m3"),
            ("pm10", pm10, "ug/m3"),
            ("no2", no2, "ppb"),
            ("o3", o3, "ppb"),
        ):
            out.append(
                AirQualityRecord(
                    metro_key=metro.key, date=d, parameter=param, value=round(value, 2), unit=unit
                )
            )
    return out


def gen_weather(metro: Metro, start: date, end: date) -> list[WeatherRecord]:
    _, base_temp, *_ = _METRO_PROFILE[metro.key]
    rng = _seed_for(metro.key, "wx")
    out: list[WeatherRecord] = []
    for d in _daterange(start, end):
        doy = d.timetuple().tm_yday
        temp = base_temp + 12 * math.sin(2 * math.pi * (doy - 100) / 365) + rng.gauss(0, 2)
        out.append(
            WeatherRecord(
                metro_key=metro.key,
                date=d,
                temp_c=round(temp, 1),
                humidity_pct=round(min(99, max(15, 60 + rng.gauss(0, 12))), 1),
                wind_kph=round(max(0, 12 + rng.gauss(0, 5)), 1),
                precip_mm=round(max(0, rng.gauss(1.5, 3)), 1),
            )
        )
    return out


def gen_demographics(metro: Metro) -> DemographicsRecord:
    _, _, base_income, base_pop, base_age = _METRO_PROFILE[metro.key]
    rng = _seed_for(metro.key, "demo")
    return DemographicsRecord(
        county_fips=metro.county_fips,
        population=int(base_pop * rng.uniform(0.97, 1.03)),
        median_age=round(base_age + rng.uniform(-1, 1), 1),
        median_income=round(base_income * rng.uniform(0.97, 1.03), 0),
    )


def gen_health(metro: Metro, mean_pm25: float, demo: DemographicsRecord) -> list[HealthRecord]:
    """Asthma/COPD prevalence as a function of pollution + income (with noise).

    This encodes the relationship the regression model is meant to recover:
    higher PM2.5 and lower income -> higher prevalence.
    """
    rng = _seed_for(metro.key, "health")
    income_factor = (75000 - demo.median_income) / 75000  # higher when poorer
    asthma = 8.0 + 0.18 * mean_pm25 + 4.5 * income_factor + rng.gauss(0, 0.4)
    copd = 5.0 + 0.10 * mean_pm25 + 3.0 * income_factor + rng.gauss(0, 0.3)
    return [
        HealthRecord(county_fips=metro.county_fips, measure="CASTHMA", prevalence_pct=round(asthma, 2)),
        HealthRecord(county_fips=metro.county_fips, measure="COPD", prevalence_pct=round(copd, 2)),
    ]


def gen_county_annual(n: int = 150) -> list[CountyAnnualRecord]:
    """National cross-section of ``n`` counties for the regression model.

    Encodes the target relationship (higher PM2.5 + NO2 and lower income/higher
    density -> higher asthma prevalence) with noise, so the model recovers
    interpretable, non-trivial coefficients.
    """
    rng = random.Random("county_annual")
    out: list[CountyAnnualRecord] = []
    for i in range(n):
        state = _STATES[i % len(_STATES)]
        fips = f"{90000 + i:05d}"  # synthetic FIPS, distinct from the real metro ones
        avg_pm25 = max(2.0, rng.gauss(11.0, 4.0))
        avg_no2 = max(1.0, rng.gauss(15.0, 5.0))
        median_income = max(28000, rng.gauss(64000, 16000))
        median_age = rng.gauss(38.0, 5.0)
        pop_density = max(20.0, rng.lognormvariate(6.0, 1.0))
        income_factor = (75000 - median_income) / 75000
        asthma = (
            7.5
            + 0.20 * avg_pm25
            + 0.05 * avg_no2
            + 4.0 * income_factor
            + 0.0008 * pop_density
            + rng.gauss(0, 0.8)
        )
        copd = 4.5 + 0.12 * avg_pm25 + 3.0 * income_factor + rng.gauss(0, 0.6)
        out.append(
            CountyAnnualRecord(
                county_fips=fips,
                state=state,
                avg_pm25=round(avg_pm25, 2),
                avg_no2=round(avg_no2, 2),
                median_income=round(median_income, 0),
                median_age=round(median_age, 1),
                pop_density=round(pop_density, 1),
                asthma_prevalence_pct=round(max(2.0, asthma), 2),
                copd_prevalence_pct=round(max(1.0, copd), 2),
            )
        )
    return out
