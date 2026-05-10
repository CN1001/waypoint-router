# Multi-Target Routing Design

## Purpose

Extend the v0.1.0 routing baseline from a fixed two-point (start → end) flow to an unlimited ordered waypoint sequence (A → B → C → D → ...). The user clicks the map to append stops, sees the route auto-calculated after two or more stops, and can remove any stop individually from the panel.

## Scope

Changes are limited to `backend/app/models.py`, `backend/app/routing.py`, `backend/app/main.py`, their tests, and `frontend/src/api.ts` plus `frontend/src/App.tsx`. No new files are required. No drag-and-drop reordering, no route mode switching, no provider changes.

## Architecture

The backend replaces the `start`/`end` two-param contract with a repeated `waypoints` query param. The frontend replaces the two-state (`start`, `end`) model with a `waypoints: LatLng[]` array. Everything else — map tiles, OSRM integration, response normalization, formatting helpers, build config — stays unchanged.

## API Contract

**Endpoint:**
```
GET /api/routes?waypoints=lat,lng&waypoints=lat,lng[&waypoints=lat,lng...]
```

Minimum 2 waypoints required. No enforced upper limit.

**Response shape** (unchanged from v0.1.0):
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

With exactly 2 waypoints: OSRM `alternatives=true` is passed — multiple route alternatives may be returned.  
With 3+ waypoints: `alternatives` is omitted — OSRM returns exactly 1 route through all stops in order.

**OSRM URL shape:**
```
/route/v1/driving/{lng},{lat};{lng},{lat};...
  ?overview=full&geometries=geojson&steps=false[&alternatives=true]
```

## Backend Changes

**`backend/app/models.py`**  
No structural changes to `Coordinate`, `Route`, or `RoutesResponse`. No new models needed — waypoint parsing happens inline in the route handler.

**`backend/app/routing.py`**  
- Replace `build_osrm_url(start, end)` with `build_osrm_url(waypoints: list[Coordinate])`. Joins all points as `lng,lat;lng,lat;...`. Appends `alternatives=true` only when `len(waypoints) == 2`.  
- Replace `fetch_route_alternatives(start, end)` with `fetch_route_alternatives(waypoints: list[Coordinate])`.

**`backend/app/main.py`**  
Replace `start: str` and `end: str` Query params with `waypoints: list[str] = Query(..., min_length=1)`. Parse each entry via `parse_coordinate_pair`. Raise HTTP 422 if fewer than 2 valid waypoints are provided or if any entry is malformed.

## Frontend Changes

**`frontend/src/api.ts`**  
Replace `fetchRoutes(start, end)` with `fetchRoutes(waypoints: LatLng[])`. Builds repeated `waypoints=lat,lng` query params using `URLSearchParams.append`.

**`frontend/src/App.tsx`**  
- Replace `start: LatLng | null` + `end: LatLng | null` state with `waypoints: LatLng[]`.  
- Click handler always appends the new point to the array.  
- `useEffect` triggers route fetch whenever `waypoints.length >= 2`.  
- Panel renders a numbered stop list (Stop 1, Stop 2, ...) with an × button on each entry. Removing a stop at any index splices the array; if the result has fewer than 2 waypoints the route clears.  
- All waypoints get markers on the map using the existing icon (no visual distinction between start, intermediate, and end markers).  
- Instruction text: "Click to set Stop 1." → "Click to set Stop 2." → "Route shown. Click to add more stops."  
- Reset clears the entire waypoints array.

## Error Handling

- Fewer than 2 waypoints in the request → HTTP 422.
- Any malformed `lat,lng` entry → HTTP 422.
- OSRM unavailable → HTTP 502 (unchanged).
- Empty OSRM result → empty `routes` array, UI shows no-route state (unchanged).

## Testing

**Backend additions:**
- `build_osrm_url` produces correct multi-stop coordinate string for 3 waypoints.
- `build_osrm_url` includes `alternatives=true` for 2 waypoints, omits it for 3+.
- API returns 422 for fewer than 2 waypoints.
- API accepts 3+ waypoints and calls OSRM with the full sequence.

**Frontend:**  
No new unit tests — the routing logic change is in state management (covered by existing manual testing). Formatting helpers are unchanged.
