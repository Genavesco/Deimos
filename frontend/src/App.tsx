import { Outlet, Link } from "react-router-dom";
import Logo from "./assets/logo.png";

export default function App(){
  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-black/40 sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <img src={Logo} alt="DEIMOS Logo" className="w-10 h-10" />
          <span className="tracking-widest font-bold">DEIMOS</span>
        </div>
        <nav className="text-sm">
          <Link className="hover:underline mr-4" to="/">Inicio</Link>
          <Link className="hover:underline" to="/sim">Comenzar simulación</Link>
        </nav>
      </header>
      <Outlet />
    </div>
  );
}
