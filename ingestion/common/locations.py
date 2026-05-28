"""Static metro reference data: the geographic scope of the project.

Kept deliberately small (a handful of US metros) so data volumes stay sane.
Each metro maps to an approximate centroid (for weather/air-quality lookups) and
a representative county FIPS (for joining CDC PLACES health data + Census ACS).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Metro:
    key: str
    name: str
    state: str
    lat: float
    lon: float
    county_fips: str  # 5-digit state+county FIPS


METROS: dict[str, Metro] = {
    "los_angeles": Metro("los_angeles", "Los Angeles", "CA", 34.0522, -118.2437, "06037"),
    "new_york": Metro("new_york", "New York", "NY", 40.7128, -74.0060, "36061"),
    "chicago": Metro("chicago", "Chicago", "IL", 41.8781, -87.6298, "17031"),
    "houston": Metro("houston", "Houston", "TX", 29.7604, -95.3698, "48201"),
    "phoenix": Metro("phoenix", "Phoenix", "AZ", 33.4484, -112.0740, "04013"),
}


def get_metros(keys: list[str]) -> list[Metro]:
    missing = [k for k in keys if k not in METROS]
    if missing:
        raise KeyError(f"Unknown metro keys: {missing}. Known: {list(METROS)}")
    return [METROS[k] for k in keys]
