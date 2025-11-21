# tests/test_smoke.py
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health_endpoint_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_metadata_ok() -> None:
    response = client.get("/")
    body = response.json()
    assert body.get("ok") is True
    assert "service" in body
    assert "version" in body
    assert "/rooms" in body.get("endpoints", [])
