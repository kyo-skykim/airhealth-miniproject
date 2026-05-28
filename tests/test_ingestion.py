from datetime import date

import pytest
from pydantic import ValidationError

from ingestion.common import sample
from ingestion.common.locations import METROS, get_metros
from ingestion.common.schemas import AirQualityRecord


def test_get_metros_rejects_unknown():
    with pytest.raises(KeyError):
        get_metros(["atlantis"])


def test_air_quality_rejects_negative_value():
    with pytest.raises(ValidationError):
        AirQualityRecord(metro_key="x", date=date(2023, 1, 1), parameter="pm25", value=-1, unit="ug/m3")


def test_sample_air_quality_is_deterministic_and_valid():
    m = METROS["los_angeles"]
    a = sample.gen_air_quality(m, date(2023, 1, 1), date(2023, 1, 3))
    b = sample.gen_air_quality(m, date(2023, 1, 1), date(2023, 1, 3))
    assert [r.model_dump() for r in a] == [r.model_dump() for r in b]  # deterministic
    assert {r.parameter for r in a} == {"pm25", "pm10", "no2", "o3"}
    assert all(r.value >= 0 for r in a)


def test_county_cross_section_has_expected_size_and_signal():
    rows = sample.gen_county_annual(150)
    assert len(rows) == 150
    assert len({r.county_fips for r in rows}) == 150  # unique FIPS
    # Higher-pollution half should have higher mean asthma prevalence (encoded signal).
    rows_sorted = sorted(rows, key=lambda r: r.avg_pm25)
    low = rows_sorted[:75]
    high = rows_sorted[75:]
    mean = lambda xs: sum(r.asthma_prevalence_pct for r in xs) / len(xs)  # noqa: E731
    assert mean(high) > mean(low)
