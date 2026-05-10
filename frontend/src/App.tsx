import L from 'leaflet';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { MapContainer, Marker, Polyline, TileLayer, useMapEvents } from 'react-leaflet';

import { fetchRoutes, type LatLng, type RouteOption } from './api';
import { formatDistance, formatDuration } from './format';

const bangkokCenter: [number, number] = [13.7563, 100.5018];
const routeColors = ['#0f766e', '#d97706', '#2563eb', '#be123c'];

const markerIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

function MapClickHandler({ onSelect }: { onSelect: (point: LatLng) => void }) {
  useMapEvents({
    click(event) {
      onSelect({ lat: event.latlng.lat, lng: event.latlng.lng });
    },
  });

  return null;
}

export default function App() {
  const [waypoints, setWaypoints] = useState<LatLng[]>([]);
  const [routes, setRoutes] = useState<RouteOption[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const instruction = useMemo(() => {
    if (waypoints.length === 0) return 'Click the map to set Stop 1.';
    if (waypoints.length === 1) return 'Click the map to set Stop 2.';
    return `Route shown. Click to add Stop ${waypoints.length + 1}.`;
  }, [waypoints.length]);

  const handleSelect = useCallback((point: LatLng) => {
    setError(null);
    setWaypoints((prev) => [...prev, point]);
  }, []);

  const removeWaypoint = useCallback((index: number) => {
    setWaypoints((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const reset = useCallback(() => {
    setWaypoints([]);
    setRoutes([]);
    setError(null);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    if (waypoints.length < 2) {
      setRoutes([]);
      return;
    }

    let isCurrent = true;
    setIsLoading(true);
    setError(null);

    fetchRoutes(waypoints)
      .then((response) => {
        if (isCurrent) {
          setRoutes(response.routes);
        }
      })
      .catch((caught: unknown) => {
        if (isCurrent) {
          setRoutes([]);
          setError(caught instanceof Error ? caught.message : 'Unable to load routes');
        }
      })
      .finally(() => {
        if (isCurrent) {
          setIsLoading(false);
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [waypoints]);

  return (
    <main className="app-shell">
      <section className="map-area" aria-label="Route planning map">
        <MapContainer center={bangkokCenter} zoom={12} scrollWheelZoom className="route-map">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapClickHandler onSelect={handleSelect} />
          {waypoints.map((wp, index) => (
            <Marker key={index} icon={markerIcon} position={[wp.lat, wp.lng]} />
          ))}
          {routes.map((route, index) => (
            <Polyline
              key={route.id}
              pathOptions={{
                color: routeColors[index % routeColors.length],
                opacity: index === 0 ? 0.95 : 0.72,
                weight: index === 0 ? 6 : 4,
              }}
              positions={route.coordinates}
            />
          ))}
        </MapContainer>
      </section>

      <aside className="control-panel" aria-label="Route controls">
        <div className="panel-heading">
          <p className="eyebrow">Multi-stop routing</p>
          <h1>Point to point routes</h1>
          <p>{instruction}</p>
        </div>

        <div className="point-list">
          {waypoints.length === 0 && (
            <p className="state-text">No stops added yet.</p>
          )}
          {waypoints.map((wp, index) => (
            <div key={index} className="waypoint-item">
              <span>Stop {index + 1}</span>
              <strong>
                {wp.lat.toFixed(5)}, {wp.lng.toFixed(5)}
              </strong>
              <button
                className="waypoint-remove"
                type="button"
                aria-label={`Remove stop ${index + 1}`}
                onClick={() => removeWaypoint(index)}
              >
                ×
              </button>
            </div>
          ))}
        </div>

        <button className="reset-button" type="button" onClick={reset}>
          Reset
        </button>

        <div className="route-results" aria-live="polite">
          <h2>Alternatives</h2>
          {isLoading && <p className="state-text">Loading route alternatives...</p>}
          {error && <p className="state-text error-text">{error}</p>}
          {!isLoading && !error && waypoints.length >= 2 && routes.length === 0 && (
            <p className="state-text">No route alternatives were returned.</p>
          )}
          {waypoints.length < 2 && (
            <p className="state-text">Add 2 or more stops to calculate a route.</p>
          )}
          {routes.map((route, index) => (
            <article className="route-item" key={route.id}>
              <div className="route-swatch" style={{ backgroundColor: routeColors[index % routeColors.length] }} />
              <div>
                <h3>Route {index + 1}</h3>
                <p>
                  {formatDistance(route.distanceMeters)} · {formatDuration(route.durationSeconds)}
                </p>
              </div>
            </article>
          ))}
        </div>
      </aside>
    </main>
  );
}
