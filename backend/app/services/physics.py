import math
from typing import Optional

EARTH_GRAVITY = 9.80665  # m/s^2
EARTH_RADIUS_M = 6_371_000.0
TARGET_DENSITY = 2700     # kg/m3, average continental crust
WATER_DENSITY = 1025      # kg/m3, mean seawater density
ICE_DENSITY = 917         # kg/m3
THERMAL_EFFICIENCY = 3e-3
THERMAL_FLUX_THRESHOLD = 15e3  # J/m^2


def mass_from_diameter_density(d_m: float, rho: float) -> float:
    """Spherical mass approximation using diameter in meters and density in kg/m3."""
    radius = d_m / 2.0
    volume = (4.0 / 3.0) * math.pi * radius ** 3
    return rho * volume


def energy_joules(d_m: float, rho: float, v_kms: float) -> float:
    """Kinetic energy following E = (pi/12) * rho * L^3 * v^2."""
    velocity_ms = v_kms * 1_000.0
    return (math.pi / 12.0) * rho * (d_m ** 3) * (velocity_ms ** 2)


def energy_megatons(d_m: float, rho: float, v_kms: float) -> float:
    return energy_joules(d_m, rho, v_kms) / 4.184e15


def gravity_at_elevation(elevation_m: float) -> float:
    radius = EARTH_RADIUS_M + elevation_m
    radius = max(radius, EARTH_RADIUS_M * 0.9)
    return EARTH_GRAVITY * (EARTH_RADIUS_M / radius) ** 2


def target_density_for_surface(terrain_type: Optional[str], elevation_m: float, landform: Optional[str]) -> float:
    if terrain_type == "water":
        return WATER_DENSITY
    if landform:
        lf = landform.lower()
        if "ice" in lf or "glacier" in lf:
            return ICE_DENSITY
        if "urban" in lf or "city" in lf:
            return 2400.0
        if "desert" in lf or "sand" in lf:
            return 2000.0
        if "forest" in lf:
            return 2200.0
    if elevation_m > 2500:
        return 2600.0
    if elevation_m < -100:
        return WATER_DENSITY
    return TARGET_DENSITY


def crater_diameter_km(d_m: float, rho_i: float, v_kms: float, angle_deg: float, ocean: bool = False,
                        rho_t: float = TARGET_DENSITY, gravity_ms2: float = EARTH_GRAVITY,
                        slope_deg: float = 0.0) -> float:
    if d_m <= 0 or v_kms <= 0 or angle_deg <= 0:
        return 0.0
    const = 1.365 if ocean else 1.161
    velocity_ms = v_kms * 1_000.0
    density_term = (rho_i / rho_t) ** (1.0 / 3.0)
    diameter_term = d_m ** 0.78
    velocity_term = velocity_ms ** 0.44
    gravity_term = gravity_ms2 ** -0.22
    angle_term = math.sin(math.radians(angle_deg)) ** (1.0 / 3.0)
    slope_factor = math.cos(math.radians(min(abs(slope_deg), 75.0)))
    slope_factor = max(slope_factor, 0.5)
    crater_m = const * density_term * diameter_term * velocity_term * gravity_term * angle_term * slope_factor
    return crater_m / 1_000.0


def thermal_radius_km(E_joules: float) -> float:
    if E_joules <= 0:
        return 0.0
    radius_m = math.sqrt((THERMAL_EFFICIENCY * E_joules) / (2.0 * math.pi * THERMAL_FLUX_THRESHOLD))
    return radius_m / 1_000.0


def thermal_flux_at_distance_jm2(E_joules: float, distance_km: float) -> float:
    if E_joules <= 0 or distance_km <= 0:
        return 0.0
    distance_m = distance_km * 1_000.0
    return (THERMAL_EFFICIENCY * E_joules) / (2.0 * math.pi * distance_m ** 2)


def shock_radius_km(E_joules: float, density_factor: float = 1.0) -> float:
    if E_joules <= 0:
        return 0.0
    density_factor = max(density_factor, 0.5)
    return 1.8 * (E_joules / 4.184e15) ** (1.0 / 3.0) * density_factor ** -0.1


def tsunami_height_m(E_joules: float, distance_km: float = 50.0, water_depth_m: Optional[float] = None) -> float:
    if E_joules <= 0:
        return 0.0
    E_mt = E_joules / 4.184e15
    if E_mt < 1:
        return 0.5
    depth_factor = 1.0
    if water_depth_m is not None:
        depth_factor = min(1.0, max(0.35, water_depth_m / 4_000.0))
    return min(80.0, 0.12 * (E_mt ** 0.5) * depth_factor * (50.0 / max(distance_km, 1.0)) ** 0.5)



def global_survival_probability(d_m: float, affected_people: float = 0.0, total_population: float = 0.0) -> float:
    if d_m < 1000:
        base = 0.9999
    elif d_m < 5000:
        base = 0.99
    elif d_m < 10000:
        base = 0.95
    else:
        base = 0.80

    if total_population > 0 and affected_people > 0:
        fraction = min(max(affected_people / total_population, 0.0), 1.0)
        scaling = max(0.0, 1.0 - fraction)
        adjusted = base * (scaling ** 0.5)
        return max(0.0001, adjusted)

    return base


def seismic_magnitude(E_joules: float) -> float:
    if E_joules <= 0:
        return 0.0
    return 0.67 * math.log10(E_joules) - 5.87


def population_density_for_surface(terrain_type: Optional[str], slope_deg: float, landform: Optional[str]) -> float:
    if terrain_type == "water":
        return 0.0
    if landform:
        lf = landform.lower()
        if any(token in lf for token in ("city", "town", "suburb", "residential")):
            return 1200.0
        if "village" in lf or "hamlet" in lf:
            return 200.0
        if "airport" in lf or "industrial" in lf:
            return 150.0
    if slope_deg > 20.0:
        return 15.0
    return 80.0
