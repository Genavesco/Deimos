import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-dist-min";
import { useMemo } from "react";
import { createPortal } from "react-dom";
import type { Data, Layout } from "plotly.js";

export type OrbitElements = {
  semi_major_axis_au: number;
  eccentricity: number;
  inclination_deg: number;
  ascending_node_deg: number;
  arg_periapsis_deg: number;
};

type OrbitModalProps = {
  open: boolean;
  onClose: () => void;
  loading: boolean;
  error: string | null;
  elements?: OrbitElements;
  asteroidName: string;
};

const Plot = createPlotlyComponent(Plotly);

const PLANET_ORBITS = [
  { name: "Mercurio", color: "#b48bff", a: 0.387098, e: 0.20563, i: 7.004, omega: 29.124, w: 48.331 },
  { name: "Venus", color: "#ff9ed1", a: 0.7233, e: 0.0068, i: 3.39, omega: 55.19, w: 76.68 },
  { name: "Tierra", color: "#4dc0ff", a: 1.00000011, e: 0.0167, i: 0.00005, omega: -11.26064, w: 102.94719 },
  { name: "Marte", color: "#ff914d", a: 1.523662, e: 0.0934, i: 1.85, omega: 49.57854, w: 336.04084 },
];

const PLANET_MARKERS = [
  { name: "Sol", color: "yellow", coords: [0, 0, 0], size: 10 },
  { name: "Mercurio", color: "#b48bff", coords: [0.387, 0, 0], size: 6 },
  { name: "Venus", color: "#ff9ed1", coords: [0.723, 0, 0], size: 6 },
  { name: "Tierra", color: "#4dc0ff", coords: [1.0, 0, 0], size: 6 },
  { name: "Marte", color: "#ff914d", coords: [1.52, 0, 0], size: 6 },
];

const SAMPLES = 500;

function degToRad(value: number): number {
  return (value * Math.PI) / 180;
}

function rotateVector(x: number, y: number, z: number, omegaRad: number, iRad: number, wRad: number): [number, number, number] {
  const cosOmega = Math.cos(omegaRad);
  const sinOmega = Math.sin(omegaRad);
  const cosI = Math.cos(iRad);
  const sinI = Math.sin(iRad);
  const cosW = Math.cos(wRad);
  const sinW = Math.sin(wRad);

  const r11 = cosOmega * cosW - sinOmega * sinW * cosI;
  const r12 = -cosOmega * sinW - sinOmega * cosW * cosI;
  const r13 = sinOmega * sinI;
  const r21 = sinOmega * cosW + cosOmega * sinW * cosI;
  const r22 = -sinOmega * sinW + cosOmega * cosW * cosI;
  const r23 = -cosOmega * sinI;
  const r31 = sinW * sinI;
  const r32 = cosW * sinI;
  const r33 = cosI;

  const xr = r11 * x + r12 * y + r13 * z;
  const yr = r21 * x + r22 * y + r23 * z;
  const zr = r31 * x + r32 * y + r33 * z;
  return [xr, yr, zr];
}

function buildOrbitTrace(elements: { a: number; e: number; i: number; omega: number; w: number }, color: string, name: string): Partial<Data> {
  const theta = Array.from({ length: SAMPLES }, (_, idx) => (idx / (SAMPLES - 1)) * Math.PI * 2);
  const a = elements.a;
  const e = elements.e;
  const b = a * Math.sqrt(1 - e * e);
  const omegaRad = degToRad(elements.omega);
  const iRad = degToRad(elements.i);
  const wRad = degToRad(elements.w);

  const rotated = theta.map((t) => {
    const x = a * Math.cos(t) - e;
    const y = b * Math.sin(t);
    return rotateVector(x, y, 0, omegaRad, iRad, wRad);
  });

  return {
    type: "scatter3d",
    x: rotated.map((p) => p[0]),
    y: rotated.map((p) => p[1]),
    z: rotated.map((p) => p[2]),
    mode: "lines",
    line: { color, width: 3 },
    name,
  };
}

function buildPlanetTraces(): Partial<Data>[] {
  return PLANET_ORBITS.map((planet) =>
    buildOrbitTrace(
      { a: planet.a, e: planet.e, i: planet.i, omega: planet.omega, w: planet.w },
      planet.color,
      `Orbita ${planet.name}`,
    ),
  );
}

function buildPlanetMarkers(): Partial<Data>[] {
  return PLANET_MARKERS.map((item) => ({
    type: "scatter3d",
    x: [item.coords[0]],
    y: [item.coords[1]],
    z: [item.coords[2]],
    mode: "markers+text",
    text: [item.name],
    textposition: "top center",
    marker: { size: item.name === "Sol" ? 10 : item.size, color: item.color },
    textfont: { color: "white" },
    name: item.name,
    hoverinfo: "text",
  }));
}

const basePlanetTraces = buildPlanetTraces();
const basePlanetMarkers = buildPlanetMarkers();

export default function OrbitModal({ open, onClose, loading, error, elements, asteroidName }: OrbitModalProps) {
  const data = useMemo(() => {
    const traces: Partial<Data>[] = [...basePlanetTraces, ...basePlanetMarkers];
    if (elements) {
      traces.push(
        buildOrbitTrace(
          {
            a: elements.semi_major_axis_au,
            e: elements.eccentricity,
            i: elements.inclination_deg,
            omega: elements.ascending_node_deg,
            w: elements.arg_periapsis_deg,
          },
          "#00e5ff",
          `Orbita ${asteroidName}`,
        ),
      );
    }
    return traces;
  }, [elements, asteroidName]);

  const layout = useMemo<Layout>(
    () => ({
      scene: {
        xaxis: { title: "X (UA)", backgroundcolor: "black", color: "white", gridcolor: "#333" },
        yaxis: { title: "Y (UA)", backgroundcolor: "black", color: "white", gridcolor: "#333" },
        zaxis: { title: "Z (UA)", backgroundcolor: "black", color: "white", gridcolor: "#333" },
        aspectmode: "data",
        dragmode: "orbit",
      },
      paper_bgcolor: "rgba(0,0,0,0.88)",
      plot_bgcolor: "rgba(0,0,0,0.88)",
      title: { text: `Orbita de ${asteroidName}`, font: { color: "white", size: 18 } },
      margin: { l: 0, r: 0, b: 0, t: 50 },
      legend: { font: { color: "white" } },
      font: { color: "white" },
    }),
    [asteroidName],
  );

  if (!open) {
    return null;
  }

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/70 px-4">
      <div className="w-full max-w-5xl rounded-2xl border border-white/15 bg-neutral-950/95 p-4 shadow-lg">
        <div className="flex items-center justify-between pb-3">
          <h3 className="text-lg font-semibold">Trayectoria 3D</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-white/20 px-3 py-1 text-sm hover:bg-white/10"
          >
            Cerrar
          </button>
        </div>
        {loading ? (
          <div className="flex h-96 items-center justify-center text-sm text-neutral-300">Cargando trayectoria...</div>
        ) : error ? (
          <div className="flex h-96 items-center justify-center text-sm text-red-300">{error}</div>
        ) : (
          <Plot
            data={data as Data[]}
            layout={layout}
            config={{ displaylogo: false, responsive: true }}
            style={{ width: "100%", height: "550px" }}
          />
        )}
      </div>
    </div>,
    document.body,
  );
}

