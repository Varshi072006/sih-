import { MapContainer, Marker, TileLayer, useMapEvents } from "react-leaflet";
import { useState } from "react";
import L from "leaflet";

const icon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

function Clicker({ onPick }) {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng, "map_selection");
    },
  });
  return null;
}

export default function MapPicker({ lat, lng, onChange }) {
  const [msg, setMsg] = useState("");
  const center = [lat || 23.35, lng || 85.33];
  return (
    <div>
      <div className="h-64 rounded overflow-hidden border">
        <MapContainer center={center} zoom={8} style={{ height: "100%", width: "100%" }}>
          <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {lat && lng && <Marker position={[lat, lng]} icon={icon} />}
          <Clicker onPick={onChange} />
        </MapContainer>
      </div>
      <div className="flex flex-wrap gap-2 mt-2">
        <button
          type="button"
          className="px-3 py-1 bg-forest-800 text-cream rounded text-sm"
          onClick={() => {
            if (!navigator.geolocation) {
              setMsg("This browser does not provide precise GPS. Select a point on the map instead.");
              return;
            }
            navigator.geolocation.getCurrentPosition(
              (pos) => {
                onChange(pos.coords.latitude, pos.coords.longitude, "browser_geolocation");
                setMsg("Approximate browser location captured. Accuracy depends on device permission.");
              },
              () => setMsg("Location permission was not granted. Please drop a pin on the map.")
            );
          }}
        >
          Use My Location
        </button>
        <span className="text-sm self-center">Lat {lat ? Number(lat).toFixed(5) : "—"} · Lng {lng ? Number(lng).toFixed(5) : "—"}</span>
      </div>
      {msg && <p className="text-sm mt-1">{msg}</p>}
    </div>
  );
}
