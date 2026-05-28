"""Source extractors. Each returns validated records and supports two modes:

* ``sample`` (default) — deterministic synthetic data, no network/keys required.
* ``api``    — live calls to the real public APIs (needs network + keys).

The live paths are intentionally thin wrappers over the shared HTTP client; the
synthetic paths live in ``ingestion.common.sample``.
"""

from __future__ import annotations

import logging
from datetime import date

from ingestion.common import sample
from ingestion.common.http import get_json, make_session
from ingestion.common.locations import Metro
from ingestion.common.schemas import (
    AirQualityRecord,
    CountyAnnualRecord,
    DemographicsRecord,
    HealthRecord,
    WeatherRecord,
)

log = logging.getLogger(__name__)

OPENAQ_URL = "https://api.openaq.org/v3"
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
CDC_PLACES_URL = "https://data.cdc.gov/resource/swc5-untb.json"
CENSUS_URL = "https://api.census.gov/data/2022/acs/acs5"


def fetch_air_quality(metros: list[Metro], start: date, end: date, mode: str) -> list[AirQualityRecord]:
    if mode == "sample":
        out: list[AirQualityRecord] = []
        for m in metros:
            out.extend(sample.gen_air_quality(m, start, end))
        return out
    # --- live OpenAQ v3 (daily aggregates per sensor) ---
    session = make_session()  # OPENAQ_API_KEY wired in via settings in production
    records: list[AirQualityRecord] = []
    for m in metros:
        data = get_json(
            session,
            f"{OPENAQ_URL}/locations",
            params={"coordinates": f"{m.lat},{m.lon}", "radius": 25000, "limit": 100},
        )
        # NOTE: full pagination + per-sensor daily aggregation omitted for brevity;
        # the sample path is the supported demo route.
        log.info("OpenAQ returned %d locations for %s", len(data.get("results", [])), m.key)
    return records


def fetch_weather(metros: list[Metro], start: date, end: date, mode: str) -> list[WeatherRecord]:
    if mode == "sample":
        out: list[WeatherRecord] = []
        for m in metros:
            out.extend(sample.gen_weather(m, start, end))
        return out
    session = make_session()
    records: list[WeatherRecord] = []
    for m in metros:
        data = get_json(
            session,
            OPEN_METEO_URL,
            params={
                "latitude": m.lat,
                "longitude": m.lon,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "daily": "temperature_2m_mean,relative_humidity_2m_mean,wind_speed_10m_max,precipitation_sum",
                "timezone": "auto",
            },
        )
        daily = data.get("daily", {})
        for i, day in enumerate(daily.get("time", [])):
            records.append(
                WeatherRecord(
                    metro_key=m.key,
                    date=date.fromisoformat(day),
                    temp_c=daily["temperature_2m_mean"][i],
                    humidity_pct=daily["relative_humidity_2m_mean"][i],
                    wind_kph=daily["wind_speed_10m_max"][i],
                    precip_mm=daily["precipitation_sum"][i],
                )
            )
    return records


def fetch_demographics(metros: list[Metro], mode: str) -> list[DemographicsRecord]:
    if mode == "sample":
        return [sample.gen_demographics(m) for m in metros]
    session = make_session()
    records: list[DemographicsRecord] = []
    for m in metros:
        state, county = m.county_fips[:2], m.county_fips[2:]
        rows = get_json(
            session,
            CENSUS_URL,
            params={
                "get": "B01003_001E,B01002_001E,B19013_001E",
                "for": f"county:{county}",
                "in": f"state:{state}",
            },
        )
        header, values = rows[0], rows[1]
        rec = dict(zip(header, values, strict=True))
        records.append(
            DemographicsRecord(
                county_fips=m.county_fips,
                population=int(rec["B01003_001E"]),
                median_age=float(rec["B01002_001E"]),
                median_income=float(rec["B19013_001E"]),
            )
        )
    return records


def fetch_county_annual(n: int, mode: str) -> list[CountyAnnualRecord]:
    if mode == "sample":
        return sample.gen_county_annual(n)
    # Live: join CDC PLACES (asthma/COPD), Census ACS (income/age/density) and
    # annual air-quality summaries across all available counties. Omitted here;
    # the sample path is the supported demo route.
    raise NotImplementedError("county_annual live extraction not implemented; use INGEST_MODE=sample")


def fetch_health(
    metros: list[Metro], mean_pm25_by_metro: dict[str, float], demographics: list[DemographicsRecord], mode: str
) -> list[HealthRecord]:
    if mode == "sample":
        demo_by_fips = {d.county_fips: d for d in demographics}
        out: list[HealthRecord] = []
        for m in metros:
            out.extend(
                sample.gen_health(m, mean_pm25_by_metro.get(m.key, 12.0), demo_by_fips[m.county_fips])
            )
        return out
    session = make_session()
    records: list[HealthRecord] = []
    for m in metros:
        rows = get_json(
            session,
            CDC_PLACES_URL,
            params={"countyfips": m.county_fips, "measureid": "CASTHMA"},
        )
        for r in rows:
            records.append(
                HealthRecord(
                    county_fips=m.county_fips,
                    measure=r.get("measureid", "CASTHMA"),
                    prevalence_pct=float(r["data_value"]),
                )
            )
    return records
