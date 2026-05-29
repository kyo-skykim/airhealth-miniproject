"""Ingestion entrypoint: extract -> validate -> write partitioned parquet raw zone.

    python -m ingestion.run_ingest            # uses .env (sample mode)
    INGEST_MODE=api python -m ingestion.run_ingest

Time-series sources (air_quality, weather) are partitioned by month to mirror a
realistic incremental layout; static sources (health, demographics) use a single
partition. Re-running overwrites partitions in place (idempotent).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date

from pydantic import BaseModel

from ingestion.common.config import settings
from ingestion.common.io import write_records
from ingestion.common.locations import get_metros
from ingestion.extractors import (
    fetch_air_quality,
    fetch_county_annual,
    fetch_demographics,
    fetch_health,
    fetch_weather,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ingest")


def _write_by_month(source: str, records: list[BaseModel]) -> int:
    buckets: dict[str, list[BaseModel]] = defaultdict(list)
    for r in records:
        d: date = r.date  # type: ignore[attr-defined]
        buckets[d.strftime("%Y-%m")].append(r)
    for part, recs in buckets.items():
        write_records(source, part, recs)
    return len(records)


def main() -> None:
    mode = settings.ingest_mode
    metros = get_metros(settings.metro_keys)
    log.info("Ingest start | mode=%s metros=%s", mode, settings.metro_keys)

    aq = fetch_air_quality(metros, settings.start_date, settings.end_date, mode)
    wx = fetch_weather(metros, settings.start_date, settings.end_date, mode)
    demo = fetch_demographics(metros, mode)

    # Health depends on observed mean PM2.5 per metro (drives the synthetic signal).
    pm25_vals: dict[str, list[float]] = defaultdict(list)
    for r in aq:
        if r.parameter == "pm25":
            pm25_vals[r.metro_key].append(r.value)
    mean_pm25 = {k: sum(v) / len(v) for k, v in pm25_vals.items()}
    health = fetch_health(metros, mean_pm25, demo, mode)

    county_annual = fetch_county_annual(150, mode)

    n_aq = _write_by_month("air_quality", aq)
    n_wx = _write_by_month("weather", wx)
    write_records("demographics", "static", demo)
    write_records("health", "static", health)
    write_records("county_annual", "static", county_annual)

    log.info(
        "Ingest done | air_quality=%d weather=%d demographics=%d health=%d county_annual=%d",
        n_aq, n_wx, len(demo), len(health), len(county_annual),
    )


if __name__ == "__main__":
    main()
