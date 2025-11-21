# tests/test_smoke.py
import pathlib
import sys

# Ensure project root is on sys.path so "import app" resolves to your local package
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
