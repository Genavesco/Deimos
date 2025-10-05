import { useEffect, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, Circle, Marker } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import EarthImpactPreview from "../components/EarthImpactPreview";


const defaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

(L.Marker.prototype as any).options.icon = defaultIcon;

const circleStyles = [
  { key: "crater", color: "#ff3b30", fill: "rgba(255, 59, 48, 0.45)", weight: 3 },
  { key: "shock", color: "#ff9f0a", fill: "rgba(255, 159, 10, 0.35)", weight: 2.5 },
  { key: "thermal", color: "#ffd60a", fill: "rgba(255, 214, 10, 0.3)", weight: 2 },
];

type SimulationResponse = {
  inputs: {
    asteroid: {
      name: string;
      diameter_m: number;
      density_kgm3: number;
      velocity_kms: number;
      angle_deg: number;
    };
    site: {
      lat: number;
      lon: number;
    };
    ocean: boolean;
  };
  environment?: {
    elevation_m: number;
    slope_deg: number;
    roughness_m: number;
    terrain_type: string;
    landform?: string | null;
    water_depth_m?: number | null;
    population_density_km2?: number | null;
    data_sources: string[];
  };
  effects: {
    energy_megatons: number;
    kinetic_energy_j: number;
    asteroid_mass_kg: number;
    crater_diameter_km: number;
    shock_radius_km: number;
    thermal_radius_km: number;
    thermal_flux_at_100km_jm2?: number | null;
    tsunami_height_m?: number | null;
    seismic_magnitude?: number | null;
    est_affected_people?: number | null;
    global_survival_prob: number;
  };
  notes: string[];
};

type LocationState = {
  result?: SimulationResponse;
};

export default function SimulationResult() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state || {}) as LocationState;
  const result = state.result;

  useEffect(() => {
    if (!result) {
      navigate("/sim", { replace: true });
    }
  }, [navigate, result]);

  if (!result) {
    return null;
  }

  const { inputs, effects, environment, notes } = result;
  const craterRadiusKm = Math.max((effects.crater_diameter_km || 0) / 2, 0);
  const shockRadiusKm = Math.max(effects.shock_radius_km || 0, craterRadiusKm);
  const thermalRadiusKm = Math.max(effects.thermal_radius_km || 0, shockRadiusKm);
  const zoneData = [
    { name: "Zona de impacto", radius: craterRadiusKm, style: circleStyles[0] },
    { name: "Onda de choque", radius: shockRadiusKm, style: circleStyles[1] },
    { name: "Zona térmica", radius: thermalRadiusKm, style: circleStyles[2] },
  ];

  const maxRadius = Math.max(...zoneData.map((zone) => zone.radius));
  const popupLegend = useMemo(() => zoneData.filter((zone) => zone.radius > 0), [zoneData]);
  const zoom = maxRadius > 400 ? 4 : maxRadius > 200 ? 5 : maxRadius > 80 ? 6 : 7;

  const formatNumber = (value: number, digits = 2) =>
    Number.isFinite(value) ? value.toFixed(digits) : "-";

  const formatProbability = (value: number) => `${(value * 100).toFixed(2)}%`;

  const formatLargeNumber = (value?: number | null) =>
    value != null ? value.toLocaleString() : "-";

  const formatLandform = (value?: string | null) => {
    if (!value) return "-";
    const cleaned = value.replace(/_/g, " ");
    const parts = cleaned.split(":").map((part) => part.trim()).filter(Boolean);
    const label = parts.length ? parts[parts.length - 1] : cleaned;
    return label
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  return (
    <div className="min-h-[calc(100vh-72px)] bg-black/60 text-neutral-100">
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Resultados de la simulación</h1>
            <p className="text-neutral-400">
              Impacto en {inputs.ocean ? "entorno oceánico" : "superficie terrestre"} – Lat {inputs.site.lat.toFixed(2)}, Lon {inputs.site.lon.toFixed(2)}
            </p>
          </div>
          <button
            type="button"
            className="px-4 py-2 rounded border border-white/20 text-sm hover:bg-white/10"
            onClick={() => navigate("/sim")}
          >
            Nueva simulación
          </button>
        </header>

        <section className="bg-neutral-950/90 border border-white/10 rounded-xl p-4 shadow-lg">
          <h2 className="text-lg font-semibold mb-3">Distribución del impacto</h2>
          <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
            <div className="h-[420px] rounded-lg overflow-hidden border border-white/10">
              <MapContainer
                center={[inputs.site.lat, inputs.site.lon]}
                zoom={zoom}
                scrollWheelZoom
                className="h-full w-full"
              >
                <TileLayer
                  url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                  attribution="&copy; OpenStreetMap contributors & CARTO"
                />
                {zoneData.map((zone) =>
                  zone.radius > 0 ? (
                    <Circle
                      key={zone.name}
                      center={[inputs.site.lat, inputs.site.lon]}
                      radius={zone.radius * 1000}
                      pathOptions={{
                        color: zone.style.color,
                        fillColor: zone.style.fill,
                        weight: zone.style.weight,
                        opacity: 0.9,
                        fillOpacity: 0.45,
                      }}
                    />
                  ) : null,
                )}
                <Marker position={[inputs.site.lat, inputs.site.lon]} />
              </MapContainer>
            </div>
            <div className="flex flex-col gap-4">
              <EarthImpactPreview lat={inputs.site.lat} lon={inputs.site.lon} craterKm={craterRadiusKm} shockKm={shockRadiusKm} thermalKm={thermalRadiusKm} />
              <div className="bg-black/40 rounded-lg border border-white/10 p-3 text-sm">
                <h4 className="font-semibold mb-2">Zonas de impacto</h4>
                <ul className="space-y-1 text-neutral-200">
                  {popupLegend.length === 0 && <li>Sin zonas afectadas registradas.</li>}
                  {popupLegend.map((zone) => (
                    <li key={zone.name} className="flex items-center gap-2">
                      <span
                        className="inline-block h-3 w-3 rounded-full"
                        style={{ backgroundColor: zone.style.color }}
                      />
                      <span>
                        {zone.name}: {zone.radius.toFixed(1)} km
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          <div className="bg-neutral-950/90 border border-white/10 rounded-xl p-4 space-y-2">
            <h3 className="text-lg font-semibold">Datos del asteroide</h3>
            <p className="text-sm text-neutral-300">{inputs.asteroid.name}</p>
            <ul className="text-sm space-y-1 text-neutral-200">
              <li>Diámetro: {inputs.asteroid.diameter_m.toLocaleString()} m</li>
              <li>Densidad: {inputs.asteroid.density_kgm3.toLocaleString()} kg/m³</li>
              <li>Velocidad: {inputs.asteroid.velocity_kms.toFixed(2)} km/s</li>
              <li>Ángulo de entrada: {inputs.asteroid.angle_deg.toFixed(1)}°</li>
              <li>Masa estimada: {formatLargeNumber(result.effects.asteroid_mass_kg)} kg</li>
            </ul>
          </div>
          <div className="bg-neutral-950/90 border border-white/10 rounded-xl p-4 space-y-2">
            <h3 className="text-lg font-semibold">Entorno del impacto</h3>
            <ul className="text-sm space-y-1 text-neutral-200">
              <li>Terreno: {environment?.terrain_type ?? "Desconocido"}</li>
              {environment?.landform && <li>Rasgo: {formatLandform(environment.landform)}</li>}
              <li>Elevación: {environment ? `${formatNumber(environment.elevation_m, 0)} m` : "-"}</li>
              <li>Pendiente media: {environment ? `${formatNumber(environment.slope_deg, 1)}°` : "-"}</li>
              <li>Densidad poblacional: {environment?.population_density_km2 ? `${formatNumber(environment.population_density_km2, 1)} hab/km²` : "Sin datos"}</li>
            </ul>
          </div>
        </section>

        <section className="bg-neutral-950/90 border border-white/10 rounded-xl p-4">
          <h3 className="text-lg font-semibold mb-3">Resultados principales</h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-neutral-200">
            <ul className="space-y-2">
              <li>Energia: {effects.energy_megatons.toFixed(2)} Mt TNT ({effects.kinetic_energy_j.toExponential(2)} J)</li>
              <li>Crater estimado: {formatNumber(effects.crater_diameter_km, 2)} km</li>
              <li>Radio de onda de choque: {formatNumber(effects.shock_radius_km, 2)} km</li>
              <li>Radio térmico: {formatNumber(effects.thermal_radius_km, 2)} km</li>
              {effects.thermal_flux_at_100km_jm2 && (
                <li>Flujo térmico a 100 km: {(effects.thermal_flux_at_100km_jm2 / 1000).toFixed(2)} kJ/m²</li>
              )}
              {effects.tsunami_height_m && <li>Tsunami estimado: {formatNumber(effects.tsunami_height_m, 2)} m</li>}
            </ul>
            <ul className="space-y-2">
              <li>Magnitud sísmica: {effects.seismic_magnitude != null ? effects.seismic_magnitude.toFixed(2) : "-"}</li>
              <li>Personas afectadas: {formatLargeNumber(effects.est_affected_people)}</li>
              <li>Probabilidad de supervivencia global: {formatProbability(effects.global_survival_prob)}</li>
            </ul>
          </div>
          {notes.length > 0 && (
            <div className="mt-4 text-xs text-neutral-400 space-y-1">
              {notes.map((note, index) => (
                <p key={index}>• {note}</p>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}





