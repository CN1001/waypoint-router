# Route Scenario Modes Design

## Purpose

Extend the routing app with a travel mode selector (driving, cycling, walking) and avoid-option checkboxes (toll, motorway, ferry). The user picks a profile and any avoids before or after setting waypoints; changing either re-triggers the route calculation automatically.

## Scope

Changes are limited to `backend/app/routing.py`, `backend/app/main.py`, their tests, `frontend/src/api.ts`, and `frontend/src/App.tsx`. No new files required. The response shape is unchanged.

## Architecture

Two optional query params are added to the existing `GET /api/routes` endpoint. Defaults preserve full backwards compatibility. The backend passes the profile into the OSRM URL path and joins exclude values as a comma-separated `exclude=` query param. The frontend adds a profile toggle and avoid checkboxes to the control panel; both are stored in component state and included in every `fetchRoutes` call.

## API Contract

```
GET /api/routes
  ?waypoints=lat,lng        (repeated, min 2 — unchanged)
  &profile=driving          (optional, default: "driving")
  &exclude=toll             (optional, repeatable)
  &exclude=motorway
```

**Valid profiles:** `driving`, `cycling`, `foot`

**Valid exclude values:** `toll`, `motorway`, `ferry`

**OSRM URL shape:**
```
/route/v1/{profile}/{lng,lat;...}
  ?overview=full&geometries=geojson&steps=false
  [&alternatives=true]
  [&exclude=toll,motorway]
```

Response shape is **unchanged** — same `routes[]` array with `id`, `distanceMeters`, `durationSeconds`, `coordinates`.

## Backend Changes

**`backend/app/routing.py`**
- `build_osrm_url(waypoints, profile, exclude)` — profile replaces the hardcoded `driving` segment; exclude values joined as `",".join(exclude)` and appended only when non-empty.
- `fetch_route_alternatives(waypoints, profile, exclude)` — passes both new params through to `build_osrm_url`.
- Add `VALID_PROFILES = {"driving", "cycling", "foot"}` and `VALID_EXCLUDES = {"toll", "motorway", "ferry"}` constants for validation.

**`backend/app/main.py`**
- Add `profile: str = Query("driving")` and `exclude: list[str] = Query([])`.
- Validate profile against `VALID_PROFILES`; raise HTTP 422 if invalid.
- Validate each exclude value against `VALID_EXCLUDES`; raise HTTP 422 if any is invalid.
- Pass both to `fetch_route_alternatives`.

## Frontend Changes

**`frontend/src/api.ts`**
- `fetchRoutes(waypoints, profile, exclude)` — appends `&profile=` and repeated `&exclude=` params.

**`frontend/src/App.tsx`**
- Add `profile: string` state (default `"driving"`) and `exclude: string[]` state (default `[]`).
- Control panel gains a profile toggle (three buttons: Driving / Cycling / Walking) and three checkboxes (Avoid tolls / Avoid motorways / Avoid ferries).
- `useEffect` dependency array includes `waypoints`, `profile`, and `exclude` — route re-fetches on any change when `waypoints.length >= 2`.
- `reset` clears waypoints and routes but keeps the selected profile and avoids (user intent, not a routing artifact).

## Error Handling

- Invalid profile → HTTP 422.
- Invalid exclude value → HTTP 422.
- All existing error behavior (OSRM unavailable → 502, empty routes → empty array) unchanged.

## Testing

**Backend additions:**
- `build_osrm_url` uses profile in URL path for cycling and foot profiles.
- `build_osrm_url` appends `exclude=toll,motorway` when exclude list is non-empty.
- `build_osrm_url` omits `exclude` param when list is empty.
- API returns 422 for unknown profile value.
- API returns 422 for unknown exclude value.
- API accepts valid profile and exclude combination and calls OSRM correctly.

**Frontend:** No new unit tests — profile/exclude state is UI interaction logic; covered by manual testing.
