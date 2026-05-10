# Multi-Target Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the fixed start/end two-point routing with an unlimited ordered waypoint list (A → B → C → ...), auto-calculating routes whenever 2+ waypoints are set.

**Architecture:** The backend `build_osrm_url` and `fetch_route_alternatives` functions are updated to accept a `list[Coordinate]` instead of two separate points; the `/api/routes` endpoint switches from `start`/`end` params to a repeated `waypoints` query param. The frontend replaces `start`/`end` state with a `waypoints: LatLng[]` array; each map click appends a stop and the panel shows numbered stops with individual × remove buttons.

**Tech Stack:** FastAPI, httpx, Pydantic, pytest (backend) · React, TypeScript, Vite, Leaflet, react-leaflet (frontend).

---

## File Structure

- **Modify:** `backend/app/routing.py` — update `build_osrm_url` and `fetch_route_alternatives` signatures
- **Modify:** `backend/app/main.py` — replace `start`/`end` Query params with `waypoints: list[str]`
- **Modify:** `backend/tests/test_routing.py` — update existing URL test + add multi-waypoint tests
- **Modify:** `backend/tests/test_api.py` — update existing coordinate test + add waypoint count tests
- **Modify:** `frontend/src/api.ts` — update `fetchRoutes` to accept `LatLng[]`
- **Modify:** `frontend/src/App.tsx` — replace two-point state with `waypoints` array, update panel UI
- **Modify:** `frontend/src/styles.css` — add `.waypoint-item` and `.waypoint-remove` styles

---

## Tasks

### Task 1: Update Backend Routing Core

**Files:**
- Modify: `backend/tests/test_routing.py`
- Modify: `backend/app/routing.py`

- [ ] **Step 1: Update the existing URL test and add two new tests in `test_routing.py`**

Replace the existing `test_build_osrm_url_uses_lng_lat_order_for_provider` and add two new tests. The full updated test file:

```python
from app.routing import build_osrm_url, normalize_osrm_routes, parse_coordinate_pair


def test_parse_coordinate_pair_returns_lat_lng_floats():
    point = parse_coordinate_pair("13.7563,100.5018")

    assert point.lat == 13.7563
    assert point.lng == 100.5018


def test_parse_coordinate_pair_rejects_out_of_range_latitude():
    try:
        parse_coordinate_pair("91,100.5018")
    except ValueError as exc:
        assert "Latitude" in str(exc)
    else:
        raise AssertionError("Expected invalid latitude to raise ValueError")


def test_parse_coordinate_pair_rejects_missing_lng_value():
    try:
        parse_coordinate_pair("13.7563")
    except ValueError as exc:
        assert "lat,lng" in str(exc)
    else:
        raise AssertionError("Expected malformed coordinate to raise ValueError")


def test_build_osrm_url_two_waypoints_uses_lng_lat_order_and_includes_alternatives():
    a = parse_coordinate_pair("13.7563,100.5018")
    b = parse_coordinate_pair("13.7367,100.5231")

    url = build_osrm_url([a, b])

    assert "100.5018,13.7563;100.5231,13.7367" in url
    assert "alternatives=true" in url
    assert "geometries=geojson" in url


def test_build_osrm_url_three_waypoints_includes_all_stops_and_omits_alternatives():
    a = parse_coordinate_pair("13.7563,100.5018")
    b = parse_coordinate_pair("13.7450,100.5100")
    c = parse_coordinate_pair("13.7367,100.5231")

    url = build_osrm_url([a, b, c])

    assert "100.5018,13.7563;100.5100,13.745;100.5231,13.7367" in url
    assert "alternatives" not in url


def test_normalize_osrm_routes_converts_geojson_lng_lat_to_leaflet_lat_lng():
    payload = {
        "routes": [
            {
                "distance": 1200.5,
                "duration": 300.0,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[100.5018, 13.7563], [100.5231, 13.7367]],
                },
            }
        ]
    }

    result = normalize_osrm_routes(payload)

    assert result["routes"][0]["id"] == "route-1"
    assert result["routes"][0]["distanceMeters"] == 1200.5
    assert result["routes"][0]["durationSeconds"] == 300.0
    assert result["routes"][0]["coordinates"] == [[13.7563, 100.5018], [13.7367, 100.5231]]
```

- [ ] **Step 2: Run tests to verify the two new URL tests fail**

Run: `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_routing.py -q`

Expected: 2 failures — `test_build_osrm_url_two_waypoints_*` and `test_build_osrm_url_three_waypoints_*` fail because `build_osrm_url` still takes two args.

- [ ] **Step 3: Update `routing.py` — change `build_osrm_url` and `fetch_route_alternatives`**

Replace the full content of `backend/app/routing.py`:

```python
from typing import Any
from urllib.parse import urlencode

import httpx

from app.models import Coordinate

OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"


class RoutingProviderError(RuntimeError):
    """Raised when OSRM cannot provide a usable route response."""


def parse_coordinate_pair(value: str) -> Coordinate:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 2 or not all(parts):
        raise ValueError("Coordinate must use lat,lng format")

    try:
        lat = float(parts[0])
        lng = float(parts[1])
    except ValueError as exc:
        raise ValueError("Coordinate values must be numbers") from exc

    if not -90 <= lat <= 90:
        raise ValueError("Latitude must be between -90 and 90")
    if not -180 <= lng <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    return Coordinate(lat=lat, lng=lng)


def build_osrm_url(waypoints: list[Coordinate]) -> str:
    coordinate_string = ";".join(f"{wp.lng},{wp.lat}" for wp in waypoints)
    params: dict[str, str] = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }
    if len(waypoints) == 2:
        params["alternatives"] = "true"
    query = urlencode(params)
    return f"{OSRM_BASE_URL}/{coordinate_string}?{query}"


def normalize_osrm_routes(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    routes = []
    for index, route in enumerate(payload.get("routes", []), start=1):
        geometry = route.get("geometry", {})
        coordinates = geometry.get("coordinates", [])
        routes.append(
            {
                "id": f"route-{index}",
                "distanceMeters": route.get("distance", 0),
                "durationSeconds": route.get("duration", 0),
                "coordinates": [[lat, lng] for lng, lat in coordinates],
            }
        )
    return {"routes": routes}


async def fetch_route_alternatives(waypoints: list[Coordinate]) -> dict[str, list[dict[str, Any]]]:
    url = build_osrm_url(waypoints)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RoutingProviderError("Routing provider is unavailable") from exc

    payload = response.json()
    if payload.get("code") not in (None, "Ok"):
        message = payload.get("message", "Routing provider could not calculate routes")
        raise RoutingProviderError(message)

    return normalize_osrm_routes(payload)
```

- [ ] **Step 4: Run tests and verify all pass**

Run: `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_routing.py -q`

Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git -C "D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing" add backend/app/routing.py backend/tests/test_routing.py
git -C "D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing" commit -m "feat: update routing core to accept waypoints list"
```

---

### Task 2: Update Backend API Endpoint

**Files:**
- Modify: `backend/tests/test_api.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Update `test_api.py` — replace existing coordinate test, add waypoint count test**

Replace the full content of `backend/tests/test_api.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_routes_endpoint_rejects_single_waypoint():
    response = client.get("/api/routes", params={"waypoints": ["13.75,100.50"]})

    assert response.status_code == 422
    assert "2 waypoints" in response.json()["detail"]


def test_routes_endpoint_rejects_invalid_waypoint_value():
    response = client.get(
        "/api/routes",
        params=[("waypoints", "91,100"), ("waypoints", "13,100")],
    )

    assert response.status_code == 422
    assert "Latitude" in response.json()["detail"]


def test_routes_endpoint_accepts_three_waypoints_and_calls_osrm(respx_mock):
    import respx
    import httpx

    osrm_url_pattern = respx.pattern.M(url__startswith="https://router.project-osrm.org")
    respx_mock.get(osrm_url_pattern).mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "Ok",
                "routes": [
                    {
                        "distance": 5000.0,
                        "duration": 600.0,
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[100.50, 13.75], [100.51, 13.76], [100.52, 13.77]],
                        },
                    }
                ],
            },
        )
    )

    response = client.get(
        "/api/routes",
        params=[
            ("waypoints", "13.75,100.50"),
            ("waypoints", "13.76,100.51"),
            ("waypoints", "13.77,100.52"),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["routes"]) == 1
    assert body["routes"][0]["distanceMeters"] == 5000.0
```

- [ ] **Step 2: Run tests to verify new tests fail**

Run: `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_api.py -q`

Expected: `test_routes_endpoint_rejects_single_waypoint`, `test_routes_endpoint_rejects_invalid_waypoint_value`, and `test_routes_endpoint_accepts_three_waypoints_and_calls_osrm` all fail because the endpoint still uses `start`/`end` params. The `test_health_endpoint_returns_ok` test passes.

- [ ] **Step 3: Check whether `respx` is available in the backend venv**

Run: `backend/.venv/Scripts/python.exe -c "import respx; print(respx.__version__)"`

If the import fails, install it:

```powershell
$env:UV_CACHE_DIR="D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing\.uv-cache"
cd "D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing\backend"
uv add --dev respx
```

Then verify: `backend/.venv/Scripts/python.exe -c "import respx; print(respx.__version__)"`

- [ ] **Step 4: Update `main.py` — replace `start`/`end` with `waypoints: list[str]`**

Replace the full content of `backend/app/main.py`:

```python
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.models import RoutesResponse
from app.routing import RoutingProviderError, fetch_route_alternatives, parse_coordinate_pair

app = FastAPI(title="Map Routing API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/routes", response_model=RoutesResponse)
async def routes(
    waypoints: list[str] = Query(..., description="Ordered waypoints as lat,lng strings, minimum 2"),
) -> dict[str, object]:
    if len(waypoints) < 2:
        raise HTTPException(status_code=422, detail="At least 2 waypoints are required")

    parsed = []
    for entry in waypoints:
        try:
            parsed.append(parse_coordinate_pair(entry))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        return await fetch_route_alternatives(parsed)
    except RoutingProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
```

- [ ] **Step 5: Run the full backend test suite**

Run: `backend/.venv/Scripts/python.exe -m pytest backend/tests -q`

Expected: all tests pass (health, routing unit tests, and API tests).

- [ ] **Step 6: Commit**

```bash
git -C "D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing" add backend/app/main.py backend/tests/test_api.py backend/pyproject.toml backend/uv.lock
git -C "D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing" commit -m "feat: update /api/routes to accept waypoints list"
```

---

### Task 3: Update Frontend API Client

**Files:**
- Modify: `frontend/src/api.ts`

- [ ] **Step 1: Replace `fetchRoutes(start, end)` with `fetchRoutes(waypoints)`**

Replace the full content of `frontend/src/api.ts`:

```typescript
export type LatLng = {
  lat: number;
  lng: number;
};

export type RouteOption = {
  id: string;
  distanceMeters: number;
  durationSeconds: number;
  coordinates: [number, number][];
};

export type RoutesResponse = {
  routes: RouteOption[];
};

export async function fetchRoutes(waypoints: LatLng[]): Promise<RoutesResponse> {
  const params = new URLSearchParams();
  for (const wp of waypoints) {
    params.append('waypoints', `${wp.lat},${wp.lng}`);
  }

  const response = await fetch(`/api/routes?${params.toString()}`);
  if (!response.ok) {
    let message = 'Route request failed';
    try {
      const body = (await response.json()) as { detail?: string };
      message = body.detail ?? message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  return response.json() as Promise<RoutesResponse>;
}
```

- [ ] **Step 2: Verify the TypeScript build still compiles (it will fail until App.tsx is updated in the next task)**

Run: `npm --prefix "D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing\frontend" run build 2>&1 | head -30`

Expected: type error on `fetchRoutes` call in `App.tsx` — this confirms the signature change is propagating. This is expected; it will be fixed in Task 4.

---

### Task 4: Update Frontend App UI

**Files:**
- Modify: `frontend/src/styles.css`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Add waypoint item styles to `styles.css`**

Append the following to the end of `frontend/src/styles.css`:

```css
.waypoint-item {
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-rows: auto auto;
  gap: 4px 8px;
  padding: 14px;
  border: 1px solid #ddd6c8;
  border-radius: 8px;
  background: #ffffff;
  align-items: start;
}

.waypoint-item span {
  grid-column: 1;
  color: #68726c;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
}

.waypoint-item strong {
  grid-column: 1;
  color: #24302c;
  font-size: 0.95rem;
  overflow-wrap: anywhere;
}

.waypoint-remove {
  grid-column: 2;
  grid-row: 1 / 3;
  align-self: center;
  background: none;
  border: none;
  color: #68726c;
  cursor: pointer;
  font-size: 1.1rem;
  line-height: 1;
  padding: 2px 4px;
  border-radius: 4px;
}

.waypoint-remove:hover {
  color: #b42318;
  background: #fef2f2;
}
```

- [ ] **Step 2: Replace `App.tsx` with the multi-waypoint implementation**

Replace the full content of `frontend/src/App.tsx`:

```tsx
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
```

- [ ] **Step 3: Run frontend tests**

Run: `npm --prefix "D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing\frontend" test -- --run`

Expected: format tests pass (no App.tsx unit tests exist).

- [ ] **Step 4: Run frontend build**

Run: `npm --prefix "D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing\frontend" run build`

Expected: build succeeds with no TypeScript errors.

- [ ] **Step 5: Commit**

```bash
git -C "D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing" add frontend/src/api.ts frontend/src/App.tsx frontend/src/styles.css
git -C "D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing" commit -m "feat: add multi-stop waypoint UI and update API client"
```

---

### Task 5: Update Docs, Changelog, and Revision Log

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `revision_log/REVISION_INDEX.md`
- Create: `revision_log/v0.2.0_multi_target_routing.md`
- Modify: `README.md`

- [ ] **Step 1: Update `CHANGELOG.md`**

Prepend a new v0.2.0 entry at the top of the file (keep the existing v0.1.0 entry below):

```markdown
## v0.2.0 - 2026-05-10 - Multi-Target Routing

- Replaced fixed start/end two-point routing with an unlimited ordered waypoint list.
- Backend `/api/routes` now accepts a repeated `waypoints=lat,lng` query param (minimum 2).
- `build_osrm_url` and `fetch_route_alternatives` updated to accept `list[Coordinate]`; `alternatives=true` is passed only for exactly 2 waypoints.
- Frontend state replaced with `waypoints: LatLng[]`; each map click appends a stop.
- Panel shows numbered stops (Stop 1, Stop 2, ...) with individual × remove buttons.
- Route auto-calculates whenever 2 or more stops are set.
```

- [ ] **Step 2: Create `revision_log/v0.2.0_multi_target_routing.md`**

```markdown
# v0.2.0 — Multi-Target Routing

**Date:** 2026-05-10
**Branch:** feat/multi-target-routing

## Summary

Extends the routing baseline from a fixed two-point flow to an unlimited ordered waypoint sequence.

## Backend Changes

- `build_osrm_url(waypoints: list[Coordinate])` replaces `build_osrm_url(start, end)`. Builds the OSRM coordinate string by joining all waypoints as `lng,lat;lng,lat;...`. Passes `alternatives=true` only when there are exactly 2 waypoints.
- `fetch_route_alternatives(waypoints: list[Coordinate])` replaces the two-arg version.
- `/api/routes` endpoint accepts `waypoints: list[str] = Query(...)` (minimum 2). Validates each entry and raises HTTP 422 for malformed or insufficient waypoints.

## Frontend Changes

- `fetchRoutes(waypoints: LatLng[])` replaces `fetchRoutes(start, end)`. Uses `URLSearchParams.append` to produce repeated `waypoints=` params.
- `App.tsx` state: `waypoints: LatLng[]` replaces `start`/`end`. Click always appends; `useEffect` triggers fetch when `waypoints.length >= 2`.
- Panel renders numbered stop rows with × remove buttons. Reset clears all stops.

## Tests Added

- `test_build_osrm_url_three_waypoints_includes_all_stops_and_omits_alternatives`
- `test_routes_endpoint_rejects_single_waypoint`
- `test_routes_endpoint_rejects_invalid_waypoint_value`
- `test_routes_endpoint_accepts_three_waypoints_and_calls_osrm`
```

- [ ] **Step 3: Update `revision_log/REVISION_INDEX.md`**

Append a new entry:

```markdown
| v0.2.0 | 2026-05-10 | Multi-Target Routing | [v0.2.0_multi_target_routing.md](v0.2.0_multi_target_routing.md) |
```

- [ ] **Step 4: Update `README.md` roadmap section**

In the `## Roadmap` section, mark the multi-target waypoints item as done and update the intro paragraph. The roadmap section should read:

```markdown
## Roadmap

- ~~Add multi-stop waypoint routing (A → B → C → ...).~~ ✓ Done in v0.2.0
- Add route scenario modes such as driving, walking, cycling, and avoid options.
- Add typed route history and saved locations.
- Add provider configuration for OSRM, GraphHopper, or self-hosted routing.
- Add end-to-end browser tests for map selection and route rendering.
```

- [ ] **Step 5: Final verification — run all tests and build**

Run backend tests:
```
backend/.venv/Scripts/python.exe -m pytest backend/tests -q
```
Expected: all pass.

Run frontend build:
```
npm --prefix "D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing\frontend" run build
```
Expected: exits 0.

- [ ] **Step 6: Commit all docs**

```bash
git -C "D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing" add CHANGELOG.md README.md revision_log/
git -C "D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing" commit -m "docs: add v0.2.0 changelog and revision log for multi-target routing"
```

---

## Self-Review

**Spec coverage:**
- ✓ Unlimited ordered waypoints — `waypoints: LatLng[]` with no cap
- ✓ Auto-calculate on 2+ waypoints — `useEffect` triggers on `waypoints.length >= 2`
- ✓ Remove-only panel — × button per stop, no reordering
- ✓ `alternatives=true` only for 2 waypoints — `build_osrm_url` conditionally adds it
- ✓ Repeated query param API — `params.append('waypoints', ...)` in `fetchRoutes`
- ✓ HTTP 422 for < 2 waypoints and malformed entries
- ✓ HTTP 502 for OSRM errors (unchanged)
- ✓ Empty routes array for no-route state (unchanged)

**Placeholder scan:** No TBDs, no vague steps, all code blocks complete.

**Type consistency:** `fetchRoutes(waypoints: LatLng[])` defined in Task 3, called identically in Task 4. `build_osrm_url(waypoints: list[Coordinate])` defined in Task 1, called in `fetch_route_alternatives` in same task. `parse_coordinate_pair` signature unchanged throughout.
