from pydantic import BaseModel, Field
from typing import List, Optional

class AsteroidInput(BaseModel):
    name: str
    diameter_m: float = Field(gt=0)
    density_kgm3: float = Field(gt=0, default=3000)
    velocity_kms: float = Field(gt=0)
    angle_deg: float = Field(ge=0, le=90, default=45)

class ImpactSite(BaseModel):
    lat: float
    lon: float

class SimulationRequest(BaseModel):
    asteroid: AsteroidInput
    site: ImpactSite
    ocean: bool = False

class EffectOutput(BaseModel):
    energy_megatons: float
    kinetic_energy_j: float
    asteroid_mass_kg: float
    crater_diameter_km: float
    shock_radius_km: float
    thermal_radius_km: float
    thermal_flux_at_100km_jm2: Optional[float] = None
    seismic_magnitude: Optional[float] = None
    tsunami_height_m: Optional[float] = None
    est_affected_people: Optional[int] = None
    global_survival_prob: Optional[float] = None

class SiteEnvironment(BaseModel):
    elevation_m: float
    slope_deg: float
    roughness_m: float
    terrain_type: str
    landform: Optional[str] = None
    country_code: Optional[str] = None
    water_depth_m: Optional[float] = None
    population_density_km2: Optional[float] = None
    data_sources: List[str] = Field(default_factory=list)

class SimulationResponse(BaseModel):
    inputs: SimulationRequest
    environment: Optional[SiteEnvironment] = None
    effects: EffectOutput
    notes: List[str] = Field(default_factory=list)
