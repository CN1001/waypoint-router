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
