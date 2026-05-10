# Map Routing Baseline

First baseline for a web routing planner. The app runs a React map UI and a FastAPI backend. Users click a start point and a target point on an OpenStreetMap map, then the app displays OSRM route alternatives.

## Purpose

- Run on a web UI.
- Use a free map source through OpenStreetMap tiles.
- Create route alternatives from point to point.
- Let the user select the first location and target location directly on the map.

## Tech Stack

- Frontend: React, TypeScript, Vite, Leaflet, React Leaflet.
- Backend: FastAPI, httpx, Pydantic.
- Routing provider: public OSRM demo server.

## Project Structure

```text
backend/   FastAPI route proxy and tests
frontend/  React map UI and tests
docs/      Design and implementation planning documents
revision_log/  Project revision history
```

## Run Backend

```powershell
cd backend
$env:UV_CACHE_DIR="..\.uv-cache"
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If PowerShell does not like the space in the cache example, use the full project path:

```powershell
$env:UV_CACHE_DIR="D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing\.uv-cache"
```

Health check:

```text
http://localhost:8000/api/health
```

## Run Frontend

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open:

```text
http://localhost:5173
```

The Vite dev server proxies `/api` requests to `http://localhost:8000`.

## Test

Backend:

```powershell
cd backend
$env:UV_CACHE_DIR="D:\01_Work\01_Projects\12_Claude-Cowork\06_Map_routing\.uv-cache"
uv run pytest tests -q
```

Frontend:

```powershell
cd frontend
npm.cmd test -- --run
npm.cmd run build
```

## OSRM Public Demo Note

This baseline uses the free OSRM public demo server. It is good for prototypes and demos, but it is not guaranteed for production traffic or heavy usage. A future version should support a self-hosted routing engine or a managed routing provider.

## Roadmap

- Add route scenario modes such as driving, walking, cycling, and avoid options.
- Add typed route history and saved locations.
- Add provider configuration for OSRM, GraphHopper, or self-hosted routing.
- Add end-to-end browser tests for map selection and route rendering.
