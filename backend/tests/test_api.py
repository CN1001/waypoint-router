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
    assert "Latitude" in response.json()["detail"]
