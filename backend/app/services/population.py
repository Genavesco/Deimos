from __future__ import annotations

from functools import lru_cache
from typing import Optional

import httpx

WORLD_BANK_INDICATOR_URL = "https://api.worldbank.org/v2/country/{country}/indicator/EN.POP.DNST"
DEFAULT_TIMEOUT = 10.0

class PopulationDensityError(RuntimeError):
    """Raised when population density data cannot be retrieved."""

@lru_cache(maxsize=128)
def get_population_density(country_code: str, lookback: int = 20) -> float:
    if not country_code:
        raise PopulationDensityError("Country code required for population density lookup")
    country = country_code.strip().lower()
    if len(country) != 2:
        country = country[:2]
    params = {
        "format": "json",
        "per_page": str(lookback),
    }
    url = WORLD_BANK_INDICATOR_URL.format(country=country)
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        raise PopulationDensityError(f"World Bank API request failed: {exc}") from exc
    if not isinstance(payload, list) or len(payload) < 2:
        raise PopulationDensityError("Unexpected World Bank API response structure")
    entries = payload[1]
    if not isinstance(entries, list):
        raise PopulationDensityError("Missing data entries in World Bank response")
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        value = entry.get("value")
        if isinstance(value, (int, float)):
            return float(value)
    raise PopulationDensityError("No population density value available for country")
