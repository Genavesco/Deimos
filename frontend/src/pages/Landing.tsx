import { useNavigate } from "react-router-dom";

export default function Landing(){
  const nav = useNavigate();
  return (
    <div className="min-h-[calc(100vh-72px)] flex flex-col items-center justify-center relative overflow-hidden">
      <h1 className="text-6xl font-extrabold tracking-[0.35em]">DEIMOS</h1>
      <p className="mt-4 max-w-xl text-center text-neutral-300">
        Visualizá y simulá escenarios de impacto de asteroides usando datos reales de NASA y USGS.
        Explorá consecuencias y evaluá estrategias de mitigación.
      </p>
      <button
        onClick={()=>nav("/sim")}
        className="mt-10 px-8 py-3 rounded-2xl bg-white/10 hover:bg-white/20 backdrop-blur border border-white/20"
      >
        Comenzar simulación
      </button>
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_center,rgba(0,120,255,0.25),transparent_60%)]" />
      <div className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 w-[1200px] h-[1200px] rounded-full blur-3xl opacity-20 bg-cyan-700/20" />
    </div>
  );
}
