import math

from fastapi import APIRouter

from app.models.schemas import (
    EffectOutput,
    SimulationRequest,
    SimulationResponse,
    SiteEnvironment,
)
from app.services import geodata, physics, population
from app.services.geodata import GeoDataError, SiteProfile
from app.services.population import PopulationDensityError

router = APIRouter()

GLOBAL_POPULATION_ESTIMATE = 8_100_000_000
GLOBAL_LAND_AREA_KM2 = 148_940_000
GLOBAL_AVERAGE_POP_DENSITY_KM2 = GLOBAL_POPULATION_ESTIMATE / GLOBAL_LAND_AREA_KM2
COASTAL_POPULATION_FRACTION = 0.4




def _build_environment_model(
    profile: SiteProfile,
    population_density: float | None,
    density_source: str | None = None,
) -> SiteEnvironment:
    sources = list(profile.data_sources)
    if density_source:
        sources.append(density_source)
    return SiteEnvironment(
        elevation_m=profile.elevation_m,
        slope_deg=profile.slope_deg,
        roughness_m=profile.roughness_m,
        terrain_type=profile.terrain_type,
        landform=profile.landform,
        country_code=profile.country_code,
        water_depth_m=profile.water_depth_m,
        population_density_km2=population_density,
        data_sources=sources,
    )


@router.post("")
async def simulate(req: SimulationRequest) -> SimulationResponse:
    profile: SiteProfile | None = None
    try:
        profile = geodata.get_site_profile(req.site.lat, req.site.lon)
    except GeoDataError:
        profile = None

    surface_density = physics.TARGET_DENSITY
    gravity_ms2 = physics.EARTH_GRAVITY
    slope_deg = 0.0
    terrain_type: str | None = None
    landform: str | None = None
    water_depth_m: float | None = None
    country_code: str | None = None

    if profile:
        surface_density = physics.target_density_for_surface(
            profile.terrain_type,
            profile.elevation_m,
            profile.landform,
        )
        gravity_ms2 = physics.gravity_at_elevation(profile.elevation_m)
        slope_deg = profile.slope_deg
        terrain_type = profile.terrain_type
        landform = profile.landform
        water_depth_m = profile.water_depth_m
        country_code = profile.country_code

    asteroid = req.asteroid
    mass_kg = physics.mass_from_diameter_density(asteroid.diameter_m, asteroid.density_kgm3)
    energy_j = physics.energy_joules(asteroid.diameter_m, asteroid.density_kgm3, asteroid.velocity_kms)
    energy_mt = energy_j / 4.184e15

    is_water_surface = req.ocean or (terrain_type == "water")
    crater_km = physics.crater_diameter_km(
        asteroid.diameter_m,
        asteroid.density_kgm3,
        asteroid.velocity_kms,
        asteroid.angle_deg,
        ocean=is_water_surface,
        rho_t=surface_density,
        gravity_ms2=gravity_ms2,
        slope_deg=slope_deg,
    )
    density_ratio = surface_density / physics.TARGET_DENSITY if surface_density else 1.0
    shock_km = physics.shock_radius_km(energy_j, density_factor=density_ratio)
    thermal_radius_km = physics.thermal_radius_km(energy_j)
    thermal_flux_100km = physics.thermal_flux_at_distance_jm2(energy_j, 100.0)
    tsunami = physics.tsunami_height_m(energy_j, water_depth_m=water_depth_m) if is_water_surface else None

    dominant_radius = max(shock_km, thermal_radius_km)
    area_km2 = math.pi * dominant_radius ** 2

    population_density = 0.0
    density_source = None
    used_population_api = False

    coastal_fraction = 1.0
    if is_water_surface:
        population_density = GLOBAL_AVERAGE_POP_DENSITY_KM2
        density_source = "Densidad costera promedio global"
        coastal_fraction = COASTAL_POPULATION_FRACTION
    else:
        api_density: float | None = None
        if country_code:
            try:
                api_density = population.get_population_density(country_code)
                used_population_api = True
                density_source = "World Bank EN.POP.DNST"
            except PopulationDensityError:
                api_density = None
        if api_density is not None and api_density > 0:
            population_density = api_density
        else:
            population_density = physics.population_density_for_surface(terrain_type, slope_deg, landform)
            density_source = "Heuristica local de densidad"

    land_limited_area = min(area_km2, GLOBAL_LAND_AREA_KM2)
    land_fraction = min(1.0, land_limited_area / GLOBAL_LAND_AREA_KM2) if GLOBAL_LAND_AREA_KM2 else 0.0
    density_estimate_people = land_limited_area * max(population_density, 0.0) * coastal_fraction
    population_cap = GLOBAL_POPULATION_ESTIMATE * land_fraction * coastal_fraction
    est_people = int(min(max(density_estimate_people, 0.0), population_cap, GLOBAL_POPULATION_ESTIMATE))

    gsurv = physics.global_survival_probability(asteroid.diameter_m, est_people, GLOBAL_POPULATION_ESTIMATE)
    seismic = physics.seismic_magnitude(energy_j)

    notes = [
        "Modelos basados en ecuaciones de Purdue Impact: crater_c y escalas de energia.",
        "Flujo termico umbral 15 kJ/m2 (quemaduras severas).",
    ]
    environment_model: SiteEnvironment | None = None
    if profile:
        environment_model = _build_environment_model(profile, population_density, density_source)
        notes.append(
            "Parametros ajustados con datos de OpenTopoData etopo1 y OpenStreetMap Nominatim."
        )
    else:
        notes.append("No se pudo obtener informacion topografica, se usaron valores por defecto.")

    if is_water_surface:
        notes.append("Impacto sobre superficie oceanica: se usa densidad costera promedio global.")
    elif used_population_api:
        notes.append("Densidad poblacional obtenida del Banco Mundial (indicador EN.POP.DNST).")
    else:
        notes.append("Densidad poblacional estimada mediante heuristicas locales.")

    if land_fraction >= 1.0:
        notes.append("Area afectada acotada por la superficie terrestre total.")
    elif population_cap < density_estimate_people:
        notes.append("Se aplico tope por fraccion de superficie terrestre para evitar sobreestimaciones.")

    if coastal_fraction < 1.0 and coastal_fraction > 0.0:
        notes.append("Solo una fraccion costera del area se considera habitada debido al impacto oceanico.")

    effects = EffectOutput(
        energy_megatons=energy_mt,
        kinetic_energy_j=energy_j,
        asteroid_mass_kg=mass_kg,
        crater_diameter_km=crater_km,
        shock_radius_km=shock_km,
        thermal_radius_km=thermal_radius_km,
        thermal_flux_at_100km_jm2=thermal_flux_100km,
        seismic_magnitude=seismic,
        tsunami_height_m=tsunami,
        est_affected_people=est_people,
        global_survival_prob=gsurv,
    )
    return SimulationResponse(inputs=req, environment=environment_model, effects=effects, notes=notes)









