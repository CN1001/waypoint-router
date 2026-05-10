from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_routes_endpoint_rejects_single_waypoint():
    response = client.get("/api/routes", params={"waypoints": ["13.75,100.50"]})

    assert response.status_code == 422
    assert "2 waypoints" in response.json()["detail"]


def test_routes_endpoint_rejects_invalid_waypoint_value():
    response = client.get(
        "/api/routes",
        params=[("waypoints", "91,100"), ("waypoints", "13,100")],
    )

    assert response.status_code == 422
    assert "Latitude" in response.json()["detail"]
