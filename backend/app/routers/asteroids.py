from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.services import physics
from app.services import sbdb

router = APIRouter(tags=["asteroids"])

DEFAULT_DENSITY = 3000.0  # kg/m3 fallback when SBDB lacks density
DEFAULT_ANGLE = 45.0  # degrees
DEFAULT_VELOCITY = 20.0  # km/s fallback when velocity is missing


def _sort_by_probability(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(items, key=lambda item: item.get("impact_probability") or 0.0, reverse=True)


@router.get("/", summary="Listado de asteroides (SBDB)")
def list_asteroids(refresh: bool = False) -> List[Dict[str, Any]]:
    try:
        summaries = sbdb.get_summary(refresh=refresh)
    except sbdb.NasaServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    ordered = _sort_by_probability(summaries)
    return [
        {
            "spkid": item["spkid"],
            "full_name": item["full_name"],
            "impact_probability": item.get("impact_probability"),
            "palermo_scale": item.get("palermo_scale"),
            "torino_scale": item.get("torino_scale"),
            "diameter_km": item.get("diameter_km"),
            "density_gcm3": item.get("density_gcm3"),
            "absolute_magnitude_h": item.get("absolute_magnitude_h"),
            "pha": item.get("pha"),
        }
        for item in ordered
    ]


@router.get("/{spkid}", summary="Detalle SBDB de un asteroide")
def get_asteroid(spkid: str, refresh: bool = False) -> Dict[str, Any]:
    try:
        detail = sbdb.get_detail(spkid, refresh=refresh)
    except sbdb.NasaResourceNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except sbdb.NasaServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    diameter_m = float(detail.get("diameter_m") or 0.0)
    density = float(detail.get("density_kgm3") or DEFAULT_DENSITY)
    velocity = float(detail.get("velocity_kms") or 0.0)
    if velocity <= 0:
        velocity = DEFAULT_VELOCITY
    angle = float(detail.get("angle_deg") or DEFAULT_ANGLE)

    mass_kg = physics.mass_from_diameter_density(diameter_m, density) if diameter_m > 0 else 0.0
    energy_j = physics.energy_joules(diameter_m, density, velocity) if diameter_m > 0 and velocity > 0 else 0.0
    energy_mt = energy_j / 4.184e15 if energy_j > 0 else 0.0

    crater_land = physics.crater_diameter_km(diameter_m, density, velocity, angle, ocean=False)
    crater_ocean = physics.crater_diameter_km(diameter_m, density, velocity, angle, ocean=True)
    shock_radius = physics.shock_radius_km(energy_j)
    thermal_radius = physics.thermal_radius_km(energy_j)
    thermal_flux_100 = physics.thermal_flux_at_distance_jm2(energy_j, 100.0)
    seismic = physics.seismic_magnitude(energy_j) if energy_j > 0 else None
    tsunami = physics.tsunami_height_m(energy_j) if energy_j > 0 else None

    response: Dict[str, Any] = {
        "spkid": detail["spkid"],
        "full_name": detail.get("full_name"),
        "pha": detail.get("pha"),
        "absolute_magnitude_h": detail.get("absolute_magnitude_h"),
        "estimated_diameter_m": diameter_m,
        "estimated_diameter_km": detail.get("diameter_km"),
        "density_kgm3": density,
        "velocity_kms": velocity,
        "angle_deg": angle,
        "impact_probability": detail.get("impact_probability"),
        "palermo_scale": detail.get("palermo_scale"),
        "torino_scale": detail.get("torino_scale"),
        "mass_kg": mass_kg,
        "energy_megatons": energy_mt,
        "kinetic_energy_j": energy_j,
        "shock_radius_km": shock_radius,
        "thermal_radius_km": thermal_radius,
        "thermal_flux_at_100km_jm2": thermal_flux_100,
        "crater_diameter_km": crater_land,
        "crater_diameter_km_ocean": crater_ocean,
        "tsunami_height_m": tsunami,
        "seismic_magnitude": seismic,
        "reported_energy_megatons": detail.get("reported_energy_megatons"),
        "reported_mass_kg": detail.get("reported_mass_kg"),
        "vi_data": detail.get("vi_data"),
        "source": detail.get("source"),
    }
    return response


@router.get("/{spkid}/orbit", summary="Elementos orbitales (SBDB)")
def get_orbit_elements_endpoint(spkid: str, refresh: bool = False) -> Dict[str, float]:
    try:
        elements = sbdb.get_orbit_elements(spkid, refresh=refresh)
    except sbdb.NasaResourceNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except sbdb.NasaServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not elements:
        raise HTTPException(status_code=404, detail="Orbit elements unavailable")
    return elements
