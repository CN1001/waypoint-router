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
