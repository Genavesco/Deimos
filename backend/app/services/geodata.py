from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

import httpx

OPENTOPODATA_URL = "https://api.opentopodata.org/v1/etopo1"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "DEIMOSImpactSim/0.1 (+https://spaceappschallenge.org/)"

class GeoDataError(RuntimeError):
    """Raised when terrain metadata cannot be retrieved."""

@dataclass
class SiteProfile:
    elevation_m: float
    slope_deg: float
    roughness_m: float
    terrain_type: str
    landform: Optional[str]
    country_code: Optional[str]
    water_depth_m: Optional[float]
    data_sources: List[str]


def _meters_per_degree(lat: float) -> tuple[float, float]:
    lat_rad = math.radians(lat)
    meters_per_deg_lat = 111_132.0 - 559.82 * math.cos(2 * lat_rad) + 1.175 * math.cos(4 * lat_rad)
    meters_per_deg_lon = 111_320.0 * math.cos(lat_rad)
    meters_per_deg_lon = max(meters_per_deg_lon, 1.0)
    return meters_per_deg_lat, meters_per_deg_lon


def _fetch_elevations(lat: float, lon: float, delta: float) -> dict[str, float]:
    samples = [
        ("center", lat, lon),
        ("north", lat + delta, lon),
        ("south", lat - delta, lon),
        ("east", lat, lon + delta),
        ("west", lat, lon - delta),
    ]
    locations = "|".join(f"{lat_val:.6f},{lon_val:.6f}" for _, lat_val, lon_val in samples)
    with httpx.Client(timeout=10.0) as client:
        response = client.get(OPENTOPODATA_URL, params={"locations": locations})
        response.raise_for_status()
        payload = response.json()
    if payload.get("status") != "OK":
        raise GeoDataError(f"OpenTopoData returned status {payload.get('status')!r}")
    results = payload.get("results") or []
    if len(results) != len(samples):
        raise GeoDataError("Incomplete elevation samples returned by OpenTopoData")
    return {
        key: float(entry.get("elevation", 0.0))
        for (key, _, _), entry in zip(samples, results)
    }


def _compute_slope_and_roughness(elevs: dict[str, float], lat: float, delta: float) -> tuple[float, float]:
    center = elevs["center"]
    neighbors = [elevs["north"], elevs["south"], elevs["east"], elevs["west"]]
    meters_per_deg_lat, meters_per_deg_lon = _meters_per_degree(lat)
    dz_dy = (elevs["north"] - elevs["south"]) / (2.0 * meters_per_deg_lat * delta)
    dz_dx = (elevs["east"] - elevs["west"]) / (2.0 * meters_per_deg_lon * delta)
    gradient = math.sqrt(dz_dx ** 2 + dz_dy ** 2)
    slope_rad = math.atan(gradient)
    slope_deg = math.degrees(slope_rad)
    mean_neighbor = sum(neighbors) / len(neighbors)
    roughness = math.sqrt(sum((value - mean_neighbor) ** 2 for value in neighbors) / len(neighbors))
    roughness = abs(roughness)
    return slope_deg, roughness


def _fetch_landform(lat: float, lon: float) -> tuple[Optional[str], Optional[str]]:
    params = {
        "format": "jsonv2",
        "lat": f"{lat:.6f}",
        "lon": f"{lon:.6f}",
        "zoom": "10",
        "namedetails": "0",
        "addressdetails": "1",
    }
    headers = {"User-Agent": USER_AGENT}
    try:
        with httpx.Client(timeout=10.0, headers=headers) as client:
            response = client.get(NOMINATIM_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError:
        return None, None
    landform: Optional[str] = None
    category = payload.get("category")
    kind = payload.get("type")
    if category and kind:
        landform = f"{category}:{kind}".replace("_", " ")
    elif payload.get("name"):
        landform = str(payload.get("name"))
    elif payload.get("display_name"):
        landform = str(payload.get("display_name")).split(",")[0].strip()
    country_code: Optional[str] = None
    address = payload.get("address")
    if isinstance(address, dict):
        code = address.get("country_code")
        if isinstance(code, str) and code:
            country_code = code.upper()
    return landform, country_code



def get_site_profile(lat: float, lon: float, delta: float = 0.01) -> SiteProfile:
    try:
        elevations = _fetch_elevations(lat, lon, delta)
    except httpx.HTTPError as exc:
        raise GeoDataError(f"Failed to query OpenTopoData: {exc}") from exc
    slope_deg, roughness_m = _compute_slope_and_roughness(elevations, lat, delta)
    elevation = elevations["center"]
    terrain_type = "water" if elevation < 0 else "land"
    water_depth = abs(elevation) if terrain_type == "water" else None
    landform, country_code = _fetch_landform(lat, lon)
    sources = ["OpenTopoData etopo1"]
    if landform or country_code:
        sources.append("OpenStreetMap Nominatim")
    return SiteProfile(
        elevation_m=elevation,
        slope_deg=slope_deg,
        roughness_m=roughness_m,
        terrain_type=terrain_type,
        landform=landform,
        country_code=country_code,
        water_depth_m=water_depth,
        data_sources=sources,
    )
