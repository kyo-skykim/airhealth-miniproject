"""Pydantic schemas validating every record before it lands in the raw zone.

Validation at the ingestion boundary keeps malformed upstream data out of the
warehouse and gives a clear contract for the dbt staging models downstream.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, field_validator


class AirQualityRecord(BaseModel):
    metro_key: str
    date: date
    parameter: str  # pm25 | pm10 | no2 | o3
    value: float
    unit: str

    @field_validator("value")
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("air quality value cannot be negative")
        return v


class WeatherRecord(BaseModel):
    metro_key: str
    date: date
    temp_c: float
    humidity_pct: float
    wind_kph: float
    precip_mm: float


class HealthRecord(BaseModel):
    county_fips: str
    measure: str  # CASTHMA | COPD
    prevalence_pct: float


class DemographicsRecord(BaseModel):
    county_fips: str
    population: int
    median_age: float
    median_income: float


class CountyAnnualRecord(BaseModel):
    """County-level annual cross-section — the regression training grain.

    A national sample of counties (CDC PLACES + Census ACS + annual air-quality
    summaries in production) giving the asthma-prevalence model enough rows.
    """

    county_fips: str
    state: str
    avg_pm25: float
    avg_no2: float
    median_income: float
    median_age: float
    pop_density: float  # people per sq mile
    asthma_prevalence_pct: float
    copd_prevalence_pct: float
