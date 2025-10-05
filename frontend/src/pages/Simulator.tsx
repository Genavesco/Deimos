import { useEffect, useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import { useNavigate } from "react-router-dom";
import { getAsteroidDetail, getAsteroidOrbit, listAsteroids, simulateImpact } from "../lib/api";
import WorldMap from "../components/ImpactSetup/WorldMap";
import Builder3D from "../components/AsteroidBuilder/Builder3D";
import OrbitModal, { type OrbitElements } from "../components/OrbitModal";

const DEFAULT_DENSITY = 3000;
const DEFAULT_ANGLE = 45;
const DEFAULT_VELOCITY = 20;

type AsteroidSummary = {
  spkid: string;
  full_name: string;
  impact_probability?: number | null;
  palermo_scale?: number | null;
  torino_scale?: number | null;
  diameter_km?: number | null;
  density_gcm3?: number | null;
  absolute_magnitude_h?: number | null;
  pha?: string | null;
};

type AsteroidDetail = AsteroidSummary & {
  estimated_diameter_m: number;
  estimated_diameter_km?: number | null;
  density_kgm3: number;
  velocity_kms: number;
  angle_deg: number;
  mass_kg: number;
  energy_megatons: number;
  kinetic_energy_j: number;
  shock_radius_km?: number | null;
  thermal_radius_km?: number | null;
  thermal_flux_at_100km_jm2?: number | null;
  crater_diameter_km?: number | null;
  crater_diameter_km_ocean?: number | null;
  tsunami_height_m?: number | null;
  seismic_magnitude?: number | null;
  vi_data?: Array<Record<string, unknown>>;
};

type AsteroidForm = {
  name: string;
  diameter_m: number;
  density_kgm3: number;
  velocity_kms: number;
  angle_deg: number;
};

type OrbitCache = Record<string, OrbitElements>;

type SimulationPayload = {
  asteroid: AsteroidForm;
  site: { lat: number; lon: number };
  ocean: boolean;
};

const massFromState = (diameter_m: number, density_kgm3: number) => {
  if (diameter_m <= 0 || density_kgm3 <= 0) return 0;
  const radius = diameter_m / 2;
  const volume = (4 / 3) * Math.PI * radius ** 3;
  return density_kgm3 * volume;
};

const energyMegatons = (diameter_m: number, density_kgm3: number, velocity_kms: number) => {
  if (diameter_m <= 0 || density_kgm3 <= 0 || velocity_kms <= 0) return 0;
  const velocity_ms = velocity_kms * 1000;
  const energy_j = (Math.PI / 12) * density_kgm3 * diameter_m ** 3 * velocity_ms ** 2;
  return energy_j / 4.184e15;
};

const formatMass = (massKg: number): { short: string; long: string } => {
  if (!Number.isFinite(massKg) || massKg <= 0) {
    return { short: "0 kg", long: "0 kg" };
  }
  const units = [
    { threshold: 1_000, label: "kg", divisor: 1 },
    { threshold: 1_000_000, label: "t", divisor: 1_000 },
    { threshold: 1_000_000_000, label: "kt", divisor: 1_000_000 },
    { threshold: 1_000_000_000_000, label: "Mt", divisor: 1_000_000_000 },
    { threshold: 1_000_000_000_000_000, label: "Gt", divisor: 1_000_000_000_000 },
    { threshold: Infinity, label: "Tt", divisor: 1_000_000_000_000_000 },
  ];
  const unit = units.find((item) => massKg < item.threshold) ?? units[units.length - 1];
  const value = massKg / unit.divisor;
  const digits = value >= 100 ? 0 : value >= 10 ? 1 : 2;
  const formatter = new Intl.NumberFormat("es-ES", { maximumFractionDigits: digits, minimumFractionDigits: 0 });
  const base = `${formatter.format(value)} ${unit.label}`;
  return { short: base, long: `${base} (${massKg.toExponential(2)} kg)` };
};

const formatProbability = (value: number | null | undefined) =>
  typeof value === "number" && Number.isFinite(value) ? value.toExponential(2) : "Sin datos";

const formatScale = (value: number | null | undefined) =>
  typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) : "Sin datos";

const formatPhaFlag = (value: string | boolean | null | undefined) => {
  if (value === true || value === "Y" || value === "y") return "Si";
  if (value === false || value === "N" || value === "n") return "No";
  return "Desconocido";
};

export default function Simulator() {
  const navigate = useNavigate();

  const [asteroids, setAsteroids] = useState<AsteroidSummary[]>([]);
  const [selectedSpk, setSelectedSpk] = useState<string>("");
  const [selectedAsteroid, setSelectedAsteroid] = useState<AsteroidDetail | null>(null);
  const [asteroidForm, setAsteroidForm] = useState<AsteroidForm>({
    name: "",
    diameter_m: 0,
    density_kgm3: DEFAULT_DENSITY,
    velocity_kms: 0,
    angle_deg: DEFAULT_ANGLE,
  });
  const [site, setSite] = useState({ lat: -31.4, lon: -64.2 });
  const [ocean, setOcean] = useState(false);
  const [loadingList, setLoadingList] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [runningSim, setRunningSim] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [orbitCache, setOrbitCache] = useState<OrbitCache>({});
  const [showOrbit, setShowOrbit] = useState(false);
  const [orbitLoading, setOrbitLoading] = useState(false);
  const [orbitError, setOrbitError] = useState<string | null>(null);

  useEffect(() => {
    setLoadingList(true);
    setListError(null);
    listAsteroids()
      .then((res) => {
        const items: AsteroidSummary[] = Array.isArray(res.data) ? res.data : [];
        const sorted = items
          .slice()
          .sort((a, b) => (b.impact_probability ?? 0) - (a.impact_probability ?? 0));
        setAsteroids(sorted);
        if (sorted.length) {
          setSelectedSpk(sorted[0].spkid);
        }
      })
      .catch(() => {
        setListError("No se pudo cargar la lista de asteroides. Verifique el backend.");
      })
      .finally(() => setLoadingList(false));
  }, []);

  useEffect(() => {
    if (!selectedSpk) {
      setSelectedAsteroid(null);
      setAsteroidForm({
        name: "",
        diameter_m: 0,
        density_kgm3: DEFAULT_DENSITY,
        velocity_kms: 0,
        angle_deg: DEFAULT_ANGLE,
      });
      return;
    }

    const summary = asteroids.find((a) => a.spkid === selectedSpk);
    const diameterFromSummary = summary?.diameter_km ? summary.diameter_km * 1000 : undefined;
    const densityFromSummary = summary?.density_gcm3 ? summary.density_gcm3 * 1000 : undefined;

    setAsteroidForm({
      name: summary?.full_name ?? "Custom",
      diameter_m: diameterFromSummary ?? 0,
      density_kgm3: densityFromSummary ?? DEFAULT_DENSITY,
      velocity_kms: DEFAULT_VELOCITY,
      angle_deg: DEFAULT_ANGLE,
    });

    setSelectedAsteroid(null);

    let cancelled = false;
    setDetailError(null);
    setLoadingDetail(true);
    getAsteroidDetail(selectedSpk)
      .then((res) => {
        if (cancelled) return;
        const detail = res.data as AsteroidDetail;
        setSelectedAsteroid(detail);

        const diameterFromDetail = detail.estimated_diameter_m ?? 0;
        const finalDiameter = diameterFromDetail > 0 ? diameterFromDetail : diameterFromSummary ?? 0;

        const densityFromDetail = detail.density_kgm3 ?? 0;
        const fallbackDensity = densityFromSummary ?? (densityFromDetail > 0 ? densityFromDetail : undefined);
        const finalDensity =
          densityFromDetail > 0 && densityFromDetail !== DEFAULT_DENSITY
            ? densityFromDetail
            : fallbackDensity ?? DEFAULT_DENSITY;

        const velocityFromDetail = detail.velocity_kms ?? 0;
        const finalVelocity = velocityFromDetail > 0 ? velocityFromDetail : DEFAULT_VELOCITY;

        const finalAngle = detail.angle_deg ?? DEFAULT_ANGLE;

        setAsteroidForm({
          name: detail.full_name ?? summary?.full_name ?? "Custom",
          diameter_m: finalDiameter,
          density_kgm3: finalDensity,
          velocity_kms: finalVelocity,
          angle_deg: finalAngle,
        });
      })
      .catch(() => {
        if (cancelled) return;
        setDetailError("No se pudo obtener el detalle del asteroide. Compruebe el backend.");
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingDetail(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedSpk, asteroids]);

  const massKg = useMemo(() => massFromState(asteroidForm.diameter_m, asteroidForm.density_kgm3), [asteroidForm]);
  const energyMt = useMemo(
    () => energyMegatons(asteroidForm.diameter_m, asteroidForm.density_kgm3, asteroidForm.velocity_kms),
    [asteroidForm],
  );
  const massFormatted = useMemo(() => formatMass(massKg), [massKg]);

  const runSim = async () => {
    if (!asteroidForm.diameter_m || !asteroidForm.velocity_kms) return;
    setRunningSim(true);
    try {
      const payload: SimulationPayload = {
        asteroid: { ...asteroidForm, name: asteroidForm.name || "Custom" },
        site,
        ocean,
      };
      const response = await simulateImpact(payload);
      navigate("/sim/result", {
        state: {
          result: response.data,
        },
      });
    } finally {
      setRunningSim(false);
    }
  };

  const handleNumberChange = (field: keyof AsteroidForm) => (event: ChangeEvent<HTMLInputElement>) => {
    const numeric = parseFloat(event.target.value);
    setAsteroidForm((prev) => ({ ...prev, [field]: Number.isFinite(numeric) ? numeric : 0 }));
  };

  const handleTrajectoryClick = async () => {
    if (!selectedSpk) return;
    setShowOrbit(true);
    if (orbitCache[selectedSpk]) {
      setOrbitError(null);
      return;
    }
    setOrbitLoading(true);
    setOrbitError(null);
    try {
      const response = await getAsteroidOrbit(selectedSpk);
      setOrbitCache((prev) => ({ ...prev, [selectedSpk]: response.data as OrbitElements }));
    } catch {
      setOrbitError("No se pudo cargar la trayectoria del asteroide.");
    } finally {
      setOrbitLoading(false);
    }
  };

  const asteroidLabel = asteroidForm.name || selectedAsteroid?.full_name || "Custom";
  const orbitElements = selectedSpk ? orbitCache[selectedSpk] : undefined;

  return (
    <div className="grid md:grid-cols-2 gap-6 p-4 min-h-[calc(100vh-72px)]">
      <div>
        <h2 className="text-2xl font-semibold">Selecciona un asteroide</h2>

        <div className="mt-2 space-y-4">
          <div>
            <label className="block text-sm mb-1">Catalogo SBDB (PHAs)</label>
            <select
              className="w-full bg-neutral-900 rounded px-3 py-2 border border-white/10"
              value={selectedSpk}
              onChange={(e) => setSelectedSpk(e.target.value)}
              disabled={loadingList}
            >
              {asteroids.map((a) => (
                <option key={a.spkid} value={a.spkid}>
                  {a.full_name}
                </option>
              ))}
            </select>
            {loadingDetail && <p className="text-xs text-neutral-400 mt-1">Cargando datos del asteroide...</p>}
            {listError && <p className="text-xs text-red-300 mt-1">{listError}</p>}
          </div>

          {detailError && <div className="text-xs text-red-400">{detailError}</div>}

          {selectedAsteroid && (
            <div className="bg-neutral-950 p-3 rounded border border-white/10 text-sm space-y-1">
              <div className="font-semibold text-neutral-200">Ficha tecnica SBDB</div>
              <div>Nombre: {selectedAsteroid.full_name}</div>
              <div>SPKID: {selectedAsteroid.spkid}</div>
              <div>Peligroso (PHA): {formatPhaFlag(selectedAsteroid.pha)}</div>
              <div>Prob. impacto (acum.): {formatProbability(selectedAsteroid.impact_probability)}</div>
              <div>Escala Palermo: {formatScale(selectedAsteroid.palermo_scale)}</div>
              <div>Escala Torino: {formatScale(selectedAsteroid.torino_scale)}</div>
              <div>Diametro catalogado (km): {(selectedAsteroid.estimated_diameter_km ?? selectedAsteroid.diameter_km ?? 0).toFixed(3)}</div>
              <div>Velocidad impacto (km/s): {(selectedAsteroid.velocity_kms ?? 0).toFixed(2)}</div>
              <div>Energia estimada: {selectedAsteroid.energy_megatons.toFixed(2)} Mt TNT</div>
              <div>Masa estimada: {formatMass(selectedAsteroid.mass_kg).long}</div>
            </div>
          )}

          <div className="bg-neutral-950 p-3 rounded border border-white/10 space-y-3">
            <div className="text-sm text-neutral-300">Asteroide seleccionado: {asteroidLabel}</div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              <div>
                <label className="text-sm">Diametro (m)</label>
                <input
                  type="number"
                  className="w-full bg-neutral-900 rounded px-2 py-1 border border-white/10"
                  value={asteroidForm.diameter_m}
                  onChange={handleNumberChange("diameter_m")}
                />
              </div>
              <div>
                <label className="text-sm">Densidad (kg/m3)</label>
                <input
                  type="number"
                  className="w-full bg-neutral-900 rounded px-2 py-1 border border-white/10"
                  value={asteroidForm.density_kgm3}
                  onChange={handleNumberChange("density_kgm3")}
                />
              </div>
              <div>
                <label className="text-sm">Velocidad (km/s)</label>
                <input
                  type="number"
                  className="w-full bg-neutral-900 rounded px-2 py-1 border border-white/10"
                  value={asteroidForm.velocity_kms}
                  onChange={handleNumberChange("velocity_kms")}
                />
              </div>
              <div>
                <label className="text-sm">Angulo (grados)</label>
                <input
                  type="number"
                  className="w-full bg-neutral-900 rounded px-2 py-1 border border-white/10"
                  value={asteroidForm.angle_deg}
                  onChange={handleNumberChange("angle_deg")}
                />
              </div>
              <div>
                <label className="text-sm">Masa (kg)</label>
                <input
                  type="text"
                  className="w-full bg-neutral-900 rounded px-2 py-1 border border-white/10 text-neutral-400"
                  value={massFormatted.short}
                  readOnly
                  title={massFormatted.long}
                />
              </div>
            </div>

            <div className="text-xs text-neutral-300 space-y-1">
              <div>Masa estimada: {massFormatted.long}</div>
              <div>Energia cinetica: {energyMt.toFixed(2)} Mt TNT</div>
            </div>

            <Builder3D />

            <button
              type="button"
              className="mt-4 w-full bg-indigo-600 px-6 py-3 text-base font-semibold rounded-lg shadow disabled:opacity-50 disabled:cursor-not-allowed hover:bg-indigo-500 transition-colors"
              onClick={handleTrajectoryClick}
              disabled={!selectedSpk}
            >
              Ver trayectoria 3D
            </button>
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-semibold">Sitio y simulacion</h2>
        <div className="mt-2 bg-neutral-950 p-3 rounded border border-white/10">
          <WorldMap pos={site} onChange={setSite} />
          <label className="flex items-center gap-2 mt-2 text-sm">
            <input type="checkbox" checked={ocean} onChange={(e) => setOcean(e.target.checked)} />
            Impacto en oceano
          </label>
          <button
            type="button"
            className="mt-4 w-full bg-indigo-600 px-6 py-3 text-base font-semibold rounded-lg shadow disabled:opacity-50 disabled:cursor-not-allowed hover:bg-indigo-500 transition-colors"
            onClick={runSim}
            disabled={runningSim || asteroidForm.diameter_m <= 0 || asteroidForm.velocity_kms <= 0}
          >
            {runningSim ? "Calculando..." : "Simular impacto"}
          </button>
        </div>

        {listError && (
          <div className="mt-3 bg-red-900/40 border border-red-400/40 text-sm text-red-200 rounded p-3">
            {listError}
          </div>
        )}
      </div>

      <OrbitModal
        open={showOrbit && !!selectedSpk}
        onClose={() => setShowOrbit(false)}
        loading={orbitLoading}
        error={orbitError}
        elements={orbitElements}
        asteroidName={asteroidLabel}
      />
    </div>
  );
}

