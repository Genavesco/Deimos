import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import type { LatLngExpression, LeafletMouseEvent } from "leaflet";


// Fix de íconos en Vite
const DefaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
(L.Marker.prototype as any).options.icon = DefaultIcon;

function Clicker({ onChange }: { onChange: (p: { lat: number; lon: number }) => void }) {
  useMapEvents({
    click(e: LeafletMouseEvent) {
      onChange({ lat: e.latlng.lat, lon: e.latlng.lng });
    },
  });
  return null;
}

export default function WorldMap({
  pos,
  onChange,
}: {
  pos: { lat: number; lon: number };
  onChange: (p: { lat: number; lon: number }) => void;
}) {
  const center: LatLngExpression = [pos.lat, pos.lon];

  return (
    <MapContainer center={center} zoom={3} style={{ height: "380px", borderRadius: 12 }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />
      <Marker position={center} />
      <Clicker onChange={onChange} />
    </MapContainer>
  );
}
