# Routing Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first GitHub-ready routing web app baseline with React, FastAPI, OpenStreetMap, and OSRM route alternatives.

**Architecture:** The React frontend handles map selection, markers, route polylines, and summaries. The FastAPI backend validates coordinates, calls the OSRM public demo service, and returns normalized route data so the frontend is insulated from routing-provider details.

**Tech Stack:** React, TypeScript, Vite, Leaflet, FastAPI, httpx, pytest, Vitest.

---

## File Structure

- `backend/app/main.py`: FastAPI application, CORS setup, health endpoint, and routes endpoint.
- `backend/app/models.py`: Pydantic models for coordinate and route responses.
- `backend/app/routing.py`: Coordinate parser, OSRM client, and OSRM response normalization.
- `backend/tests/test_routing.py`: Backend unit tests for parsing and route normalization.
- `backend/tests/test_api.py`: Backend API tests.
- `frontend/src/App.tsx`: Main map UI and routing workflow.
- `frontend/src/api.ts`: Backend API client.
- `frontend/src/format.ts`: Distance and duration formatting helpers.
- `frontend/src/format.test.ts`: Frontend utility tests.
- `frontend/src/styles.css`: Application layout and map styling.
- `README.md`: Setup and project overview.
- `CHANGELOG.md`: Version summary.
- `revision_log/REVISION_INDEX.md`: Version index.
- `revision_log/v0.1.0_routing_baseline.md`: Detailed baseline revision entry.

## Tasks

### Task 1: Backend Routing Core

**Files:**
- Create: `backend/app/models.py`
- Create: `backend/app/routing.py`
- Create: `backend/tests/test_routing.py`

- [ ] **Step 1: Write failing tests for coordinate parsing and OSRM normalization**

```python
from app.routing import parse_coordinate_pair, normalize_osrm_routes


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

- [ ] **Step 2: Run tests and verify they fail because files do not exist**

Run: `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_routing.py -q`

Expected: FAIL with import or missing module error.

- [ ] **Step 3: Implement models and routing helpers**

Create Pydantic coordinate and route models. Implement strict `lat,lng` parsing, range validation, and OSRM route normalization.

- [ ] **Step 4: Run tests and verify they pass**

Run: `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_routing.py -q`

Expected: PASS.

### Task 2: Backend API

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/tests/test_api.py`
- Modify: `backend/app/routing.py`

- [ ] **Step 1: Write failing API tests**

```python
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_routes_endpoint_rejects_invalid_coordinate():
    response = client.get("/api/routes", params={"start": "91,100", "end": "13,100"})

    assert response.status_code == 422
```

- [ ] **Step 2: Run tests and verify they fail because API does not exist**

Run: `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_api.py -q`

Expected: FAIL with missing `app.main`.

- [ ] **Step 3: Implement FastAPI app and route endpoint**

Add CORS, `/api/health`, and `/api/routes`. The route endpoint calls the OSRM client and maps validation errors to HTTP 422 and provider errors to HTTP 502.

- [ ] **Step 4: Run backend test suite**

Run: `backend/.venv/Scripts/python.exe -m pytest backend/tests -q`

Expected: PASS.

### Task 3: Frontend Utilities

**Files:**
- Create: `frontend/src/format.ts`
- Create: `frontend/src/format.test.ts`

- [ ] **Step 1: Write failing formatting tests**

```typescript
import { describe, expect, it } from 'vitest';
import { formatDistance, formatDuration } from './format';

describe('formatDistance', () => {
  it('formats meters below one kilometer', () => {
    expect(formatDistance(850)).toBe('850 m');
  });

  it('formats kilometers with one decimal place', () => {
    expect(formatDistance(1234)).toBe('1.2 km');
  });
});

describe('formatDuration', () => {
  it('formats short durations in minutes', () => {
    expect(formatDuration(300)).toBe('5 min');
  });

  it('formats long durations in hours and minutes', () => {
    expect(formatDuration(5460)).toBe('1 hr 31 min');
  });
});
```

- [ ] **Step 2: Run tests and verify they fail because the module does not exist**

Run: `npm --prefix frontend test -- --run`

Expected: FAIL with missing `format` module.

- [ ] **Step 3: Implement formatting helpers**

Implement `formatDistance` and `formatDuration` in `frontend/src/format.ts`.

- [ ] **Step 4: Run frontend tests**

Run: `npm --prefix frontend test -- --run`

Expected: PASS.

### Task 4: Frontend App

**Files:**
- Create: `frontend/src/api.ts`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/styles.css`
- Create: `frontend/index.html`
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`

- [ ] **Step 1: Implement API client**

Create a typed `fetchRoutes(start, end)` helper that calls `/api/routes` with `lat,lng` query parameters and throws a readable error for non-OK responses.

- [ ] **Step 2: Implement map UI**

Render a Leaflet map, start/target markers, route polylines, route summaries, loading/error/empty states, and reset action.

- [ ] **Step 3: Run frontend build**

Run: `npm --prefix frontend run build`

Expected: PASS.

### Task 5: Project Metadata and Revision Log

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `CHANGELOG.md`
- Create: `revision_log/REVISION_INDEX.md`
- Create: `revision_log/v0.1.0_routing_baseline.md`

- [ ] **Step 1: Add GitHub-ready docs**

Write setup instructions for backend and frontend, explain the OSRM public demo limitation, and list the roadmap.

- [ ] **Step 2: Add version history**

Create v0.1.0 changelog and revision log entries for the routing baseline.

- [ ] **Step 3: Final verification**

Run backend tests and frontend build:

```bash
backend/.venv/Scripts/python.exe -m pytest backend/tests -q
npm --prefix frontend run build
```

Expected: both commands exit 0.

- [ ] **Step 4: Commit baseline**

```bash
git add .
git commit -m "feat: add routing baseline - v0.1.0"
```

## Self-Review

The plan covers all approved design sections: frontend map interaction, backend route proxy, OSRM alternatives, error handling, project docs, and revision history. No placeholders remain. Coordinate data consistently uses `lat,lng` strings at API boundaries and `[lat, lng]` arrays in frontend route geometry.
