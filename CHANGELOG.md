# Changelog

## v0.2.0 - 2026-05-10 - Multi-Target Routing

- Replaced fixed start/end two-point routing with an unlimited ordered waypoint list.
- Backend `/api/routes` now accepts a repeated `waypoints=lat,lng` query param (minimum 2).
- `build_osrm_url` and `fetch_route_alternatives` updated to accept `list[Coordinate]`; `alternatives=true` is passed only for exactly 2 waypoints.
- Frontend state replaced with `waypoints: LatLng[]`; each map click appends a stop.
- Panel shows numbered stops (Stop 1, Stop 2, ...) with individual × remove buttons.
- Route auto-calculates whenever 2 or more stops are set.

## v0.1.0 - 2026-05-10 - Routing Baseline

- Added React and Leaflet web UI for selecting start and target points on OpenStreetMap.
- Added FastAPI backend with health and route alternatives endpoints.
- Added OSRM public demo routing integration through the backend.
- Added backend tests, frontend utility tests, project documentation, and revision log.
