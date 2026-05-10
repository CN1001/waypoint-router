# Routing Baseline Design

## Purpose

Create the first GitHub-ready baseline for a web routing application. The app lets a user select a start location and a target location on a free map, then displays possible point-to-point route alternatives.

## Scope

The baseline includes a React web UI, a FastAPI backend, OpenStreetMap map tiles, and route alternatives from the public OSRM demo service. It is intended for prototype and portfolio use, not heavy production traffic.

## Architecture

The frontend owns map interaction, marker display, route drawing, and route summaries. The backend owns coordinate validation, OSRM request construction, OSRM response normalization, and a stable API contract for the UI. Keeping OSRM behind the backend lets future versions replace the routing provider without rewriting the map UI.

## Frontend

The React app renders a full-page Leaflet map with a compact control panel. The user clicks the map once to set the start point and once to set the target point. After both points are set, the frontend calls `/api/routes` and draws each returned alternative route in a distinct color. The panel lists each route's distance and duration and includes a reset action.

## Backend

FastAPI exposes:

- `GET /api/health` for a simple health check.
- `GET /api/routes?start=lat,lng&end=lat,lng` for route alternatives.

The route endpoint validates latitude and longitude ranges, calls `https://router.project-osrm.org/route/v1/driving/{lng},{lat};{lng},{lat}` with `overview=full`, `geometries=geojson`, `alternatives=true`, and `steps=false`, then returns normalized route objects.

## Data Contract

Successful route response:

```json
{
  "routes": [
    {
      "id": "route-1",
      "distanceMeters": 1234.5,
      "durationSeconds": 321.0,
      "coordinates": [[13.75, 100.50], [13.76, 100.51]]
    }
  ]
}
```

Coordinates are returned as `[lat, lng]` pairs for direct Leaflet use.

## Error Handling

Invalid coordinates return HTTP 422 with a clear validation error. OSRM network or provider failures return HTTP 502. Empty OSRM results return an empty `routes` array so the UI can show a no-route state.

## Testing

Backend tests cover coordinate parsing, invalid coordinate rejection, OSRM response normalization, and route service behavior with a mocked HTTP transport. Frontend tests cover route formatting utilities. Manual verification covers map selection and route rendering because Leaflet rendering is browser-dependent.

## GitHub Baseline

The repository includes:

- `README.md` with purpose, setup, run commands, and roadmap.
- `.gitignore`.
- `backend/` FastAPI app and tests.
- `frontend/` React app and tests.
- `docs/` design and implementation plan.
- `revision_log/` and `CHANGELOG.md` for version history.
