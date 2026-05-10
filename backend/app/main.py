from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.models import RoutesResponse
from app.routing import RoutingProviderError, fetch_route_alternatives, parse_coordinate_pair

app = FastAPI(title="Map Routing API", version="0.1.0")

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
    start: str = Query(..., description="Start coordinate as lat,lng"),
    end: str = Query(..., description="Target coordinate as lat,lng"),
) -> dict[str, object]:
    try:
        start_point = parse_coordinate_pair(start)
        end_point = parse_coordinate_pair(end)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        return await fetch_route_alternatives(start_point, end_point)
    except RoutingProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
