from pydantic import BaseModel


class Coordinate(BaseModel):
    lat: float
    lng: float


class Route(BaseModel):
    id: str
    distanceMeters: float
    durationSeconds: float
    coordinates: list[list[float]]


class RoutesResponse(BaseModel):
    routes: list[Route]
