from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "paywise-api"
    assert payload["version"] == "0.1.0"
    assert payload["timestamp"].endswith("Z")


def test_root_advertises_api_links() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "Paywise",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
