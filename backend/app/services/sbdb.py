from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import httpx

SUMMARY_URL = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
SUMMARY_PARAMS = {
    "fields": "full_name,spkid,a,e,q,i,w,per,per_y,n,H,diameter,GM,density,albedo",
    "sb-group": "pha",
}
DETAIL_URL = "https://ssd-api.jpl.nasa.gov/sbdb.api"
CACHE_MAX_AGE = 12 * 3600  # 12 hours
CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "sbdb"
SUMMARY_CACHE = CACHE_DIR / "pha_summary.json"
DETAIL_CACHE_DIR = CACHE_DIR / "details"

NUMERIC_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")
DEFAULT_DENSITY_KGM3 = 3000.0
DEFAULT_ANGLE_DEG = 45.0


class NasaServiceError(RuntimeError):
    """Base error raised when NASA SBDB queries fail."""


class NasaResourceNotFound(NasaServiceError):
    """Raised when a requested SBDB resource is missing."""


@dataclass
class SummaryRecord:
    spkid: str
    full_name: str
    absolute_magnitude_h: Optional[float]
    diameter_km: Optional[float]
    density_gcm3: Optional[float]
    impact_probability: Optional[float]
    palermo_scale: Optional[float]
    torino_scale: Optional[float]
    pha: Optional[str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "spkid": self.spkid,
            "full_name": self.full_name,
            "absolute_magnitude_h": self.absolute_magnitude_h,
            "diameter_km": self.diameter_km,
            "density_gcm3": self.density_gcm3,
            "impact_probability": self.impact_probability,
            "palermo_scale": self.palermo_scale,
            "torino_scale": self.torino_scale,
            "pha": self.pha,
        }


@dataclass
class VIEntry:
    date: Optional[str]
    ip: Optional[float]
    ps: Optional[float]
    ts: Optional[float]
    energy_mt: Optional[float]
    distance_au: Optional[float]
    v_inf_kms: Optional[float]
    v_imp_kms: Optional[float]
    h_mag: Optional[float]
    diameter_m: Optional[float]
    mass_kg: Optional[float]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "impact_probability": self.ip,
            "palermo_scale": self.ps,
            "torino_scale": self.ts,
            "energy_megatons": self.energy_mt,
            "distance_au": self.distance_au,
            "v_inf_kms": self.v_inf_kms,
            "v_imp_kms": self.v_imp_kms,
            "h_mag": self.h_mag,
            "diameter_m": self.diameter_m,
            "mass_kg": self.mass_kg,
        }


@dataclass
class DetailRecord:
    spkid: str
    full_name: str
    pha: Optional[str]
    absolute_magnitude_h: Optional[float]
    diameter_km: Optional[float]
    diameter_m: Optional[float]
    density_kgm3: Optional[float]
    velocity_kms: Optional[float]
    impact_probability: Optional[float]
    palermo_scale: Optional[float]
    torino_scale: Optional[float]
    reported_energy_mt: Optional[float]
    reported_mass_kg: Optional[float]
    vi_data: List[Dict[str, Any]]
    source: str = "NASA SBDB"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "spkid": self.spkid,
            "full_name": self.full_name,
            "pha": self.pha,
            "absolute_magnitude_h": self.absolute_magnitude_h,
            "diameter_km": self.diameter_km,
            "diameter_m": self.diameter_m,
            "density_kgm3": self.density_kgm3,
            "velocity_kms": self.velocity_kms,
            "impact_probability": self.impact_probability,
            "palermo_scale": self.palermo_scale,
            "torino_scale": self.torino_scale,
            "reported_energy_megatons": self.reported_energy_mt,
            "reported_mass_kg": self.reported_mass_kg,
            "vi_data": self.vi_data,
            "source": self.source,
        }


def _ensure_directories() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DETAIL_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _is_fresh(path: Path, now: Optional[float] = None) -> bool:
    if not path.exists():
        return False
    now = now or time.time()
    try:
        return (now - path.stat().st_mtime) < CACHE_MAX_AGE
    except FileNotFoundError:
        return False


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def _save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        match = NUMERIC_RE.search(cleaned)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None
    return None


def _extract_phys_value(raw: Any, key: str) -> Optional[float]:
    phys = raw.get("phys_par") if isinstance(raw, dict) else None
    if isinstance(phys, dict):
        return _to_float(phys.get(key))
    if isinstance(phys, list):
        for item in phys:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("key")
            if name == key:
                return _to_float(item.get("value") or item.get("val"))
    return None


def _normalize_summary_rows(fields: Iterable[str], rows: Iterable[Iterable[Any]]) -> List[SummaryRecord]:
    normalized: List[SummaryRecord] = []
    field_list = list(fields)
    for row in rows:
        mapping = dict(zip(field_list, row))
        spkid = str(mapping.get("spkid", "")).strip()
        full_name = str(mapping.get("full_name", "")).strip()
        if not spkid or not full_name:
            continue
        record = SummaryRecord(
            spkid=spkid,
            full_name=full_name,
            absolute_magnitude_h=_to_float(mapping.get("H") or mapping.get("h")),
            diameter_km=_to_float(mapping.get("diameter")),
            density_gcm3=_to_float(mapping.get("density")),
            impact_probability=_to_float(mapping.get("ip")),
            palermo_scale=_to_float(mapping.get("ps")),
            torino_scale=_to_float(mapping.get("ts")),
            pha=(mapping.get("pha") or mapping.get("PHA") or None),
        )
        normalized.append(record)
    return normalized


def fetch_summary(refresh: bool = False) -> List[Dict[str, Any]]:
    _ensure_directories()
    if not refresh and _is_fresh(SUMMARY_CACHE):
        cached = _load_json(SUMMARY_CACHE)
        if isinstance(cached, dict) and "items" in cached:
            return cached["items"]
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(SUMMARY_URL, params=SUMMARY_PARAMS)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise NasaServiceError(f"SBDB summary request failed: {exc}") from exc
    except httpx.HTTPError as exc:
        raise NasaServiceError(f"SBDB summary request error: {exc}") from exc

    payload = response.json()
    records = _normalize_summary_rows(payload.get("fields", []), payload.get("data", []))
    items = [record.as_dict() for record in records]
    _save_json(SUMMARY_CACHE, {"fetched_at": time.time(), "items": items})
    return items


def _normalize_vi_data(raw_vi: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for entry in raw_vi or []:
        if not isinstance(entry, dict):
            continue
        vi = VIEntry(
            date=entry.get("date"),
            ip=_to_float(entry.get("ip")),
            ps=_to_float(entry.get("ps")),
            ts=_to_float(entry.get("ts")),
            energy_mt=_to_float(entry.get("energy")),
            distance_au=_to_float(entry.get("dist")),
            v_inf_kms=_to_float(entry.get("v_inf")),
            v_imp_kms=_to_float(entry.get("v_imp")),
            h_mag=_to_float(entry.get("h")),
            diameter_m=_to_float(entry.get("diam")),
            mass_kg=_to_float(entry.get("mass")),
        )
        normalized.append(vi.as_dict())
    return normalized


def _select_primary_vi(entries: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not entries:
        return None
    return max(entries, key=lambda e: e.get("impact_probability") or 0.0)


def _convert_density(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    # SBDB densities are expressed in g/cm^3; convert to kg/m^3
    return value * 1000.0


def _normalize_detail(raw: Dict[str, Any], spkid: str) -> DetailRecord:
    obj = raw.get("object") if isinstance(raw, dict) else {}
    full_name = (
        (obj or {}).get("fullname")
        or raw.get("fullname")
        or (obj or {}).get("full-name")
        or spkid
    )
    vi_data = _normalize_vi_data(raw.get("vi_data") if isinstance(raw, dict) else None)
    primary_vi = _select_primary_vi(vi_data)

    diameter_km = _extract_phys_value(raw, "diameter")
    diameter_m: Optional[float]
    if diameter_km is not None:
        diameter_m = diameter_km * 1000.0
    else:
        diameter_m = primary_vi.get("diameter_m") if primary_vi else None
        if diameter_m is not None:
            diameter_km = diameter_m / 1000.0

    density = _extract_phys_value(raw, "density")
    density_kgm3 = _convert_density(density) if density is not None else None

    velocity_kms = None
    if primary_vi:
        velocity_kms = primary_vi.get("v_imp_kms") or primary_vi.get("v_inf_kms")

    impact_probability = primary_vi.get("impact_probability") if primary_vi else None
    palermo_scale = primary_vi.get("palermo_scale") if primary_vi else None
    torino_scale = primary_vi.get("torino_scale") if primary_vi else None
    reported_energy_mt = primary_vi.get("energy_megatons") if primary_vi else None
    reported_mass_kg = primary_vi.get("mass_kg") if primary_vi else None

    absolute_mag = _to_float(obj.get("h") or obj.get("H"))
    pha = obj.get("pha") if isinstance(obj, dict) else None

    return DetailRecord(
        spkid=str(spkid),
        full_name=str(full_name),
        pha=pha,
        absolute_magnitude_h=absolute_mag,
        diameter_km=diameter_km,
        diameter_m=diameter_m,
        density_kgm3=density_kgm3,
        velocity_kms=velocity_kms,
        impact_probability=impact_probability,
        palermo_scale=palermo_scale,
        torino_scale=torino_scale,
        reported_energy_mt=reported_energy_mt,
        reported_mass_kg=reported_mass_kg,
        vi_data=vi_data,
    )


def fetch_detail(spkid: str, refresh: bool = False) -> Dict[str, Any]:
    if not spkid:
        raise ValueError("spkid is required")
    _ensure_directories()
    cache_path = DETAIL_CACHE_DIR / f"{spkid}.json"
    if not refresh and _is_fresh(cache_path):
        cached = _load_json(cache_path)
        if isinstance(cached, dict):
            if "normalized" in cached:
                return cached["normalized"]
            if "data" in cached:
                return _normalize_detail(cached["data"], spkid).as_dict()

    params = {
        "sstr": str(spkid),
        "phys-par": "1",
        "vi-data": "1",
        "discovery": "1",
    }
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(DETAIL_URL, params=params)
        if response.status_code == 404:
            raise NasaResourceNotFound(f"Asteroid with spkid={spkid} not found")
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise NasaServiceError(f"SBDB detail request failed: {exc}") from exc
    except httpx.HTTPError as exc:
        raise NasaServiceError(f"SBDB detail request error: {exc}") from exc

    raw_payload = response.json()
    if isinstance(raw_payload, dict) and raw_payload.get("message"):
        message = raw_payload.get("message")
        if "not found" in str(message).lower():
            raise NasaResourceNotFound(str(message))

    normalized = _normalize_detail(raw_payload, spkid)
    _save_json(cache_path, {
        "fetched_at": time.time(),
        "data": raw_payload,
        "normalized": normalized.as_dict(),
    })
    return normalized.as_dict()


def get_detail(spkid: str, refresh: bool = False) -> Dict[str, Any]:
    payload = fetch_detail(spkid, refresh=refresh)
    if "density_kgm3" not in payload or payload["density_kgm3"] is None:
        payload["density_kgm3"] = DEFAULT_DENSITY_KGM3
    if payload.get("velocity_kms") in (None, 0):
        payload["velocity_kms"] = 20.0  # heuristic fallback
    if payload.get("diameter_m") in (None, 0):
        payload["diameter_m"] = 100.0
        payload["diameter_km"] = payload["diameter_m"] / 1000.0
    payload.setdefault("angle_deg", DEFAULT_ANGLE_DEG)
    return payload



def _extract_orbit_mapping(orbit: Any) -> dict[str, float]:
    mapping: dict[str, float] = {}
    if isinstance(orbit, dict):
        elements = orbit.get("elements")
        if isinstance(elements, list):
            for item in elements:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                value = item.get("value")
                try:
                    if name is not None and value is not None:
                        mapping[name.lower()] = float(value)
                except (TypeError, ValueError):
                    continue
        for key, value in orbit.items():
            try:
                mapping.setdefault(str(key).lower(), float(value))
            except (TypeError, ValueError):
                continue
    return mapping


def get_orbit_elements(spkid: str, refresh: bool = False) -> dict[str, float]:
    if not spkid:
        raise ValueError("spkid is required")
    _ensure_directories()
    cache_path = DETAIL_CACHE_DIR / f"{spkid}.json"
    if refresh or not _is_fresh(cache_path):
        fetch_detail(spkid, refresh=refresh)
    else:
        try:
            fetch_detail(spkid, refresh=False)
        except NasaServiceError:
            fetch_detail(spkid, refresh=True)
    raw_payload: dict[str, Any] | None = None
    if cache_path.exists():
        cached = _load_json(cache_path)
        if isinstance(cached, dict):
            raw_payload = cached.get("data")
    if not isinstance(raw_payload, dict):
        raise NasaServiceError("Orbit data not available")
    orbit_data = raw_payload.get("orbit")
    if not orbit_data:
        return {}
    mapping = _extract_orbit_mapping(orbit_data)

    def _pick(*keys: str) -> float | None:
        for key in keys:
            value = mapping.get(key.lower())
            if value is not None:
                return value
        return None

    a = _pick("a")
    e = _pick("e")
    i_deg = _pick("i")
    om_deg = _pick("om", "node", "ascending_node")
    w_deg = _pick("w", "argp", "pericenter", "argument_of_periapsis")

    if None in (a, e, i_deg, om_deg, w_deg):
        raise NasaServiceError("Incomplete orbit elements")

    return {
        "semi_major_axis_au": float(a),
        "eccentricity": float(e),
        "inclination_deg": float(i_deg),
        "ascending_node_deg": float(om_deg),
        "arg_periapsis_deg": float(w_deg),
    }

def get_summary(refresh: bool = False) -> List[Dict[str, Any]]:
    items = fetch_summary(refresh=refresh)
    if not items:
        raise NasaServiceError("No asteroid data retrieved from SBDB")
    return items


