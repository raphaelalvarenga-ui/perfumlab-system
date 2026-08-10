from fastapi.testclient import TestClient

from app.main_api import app


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Perfum Lab API",
        "version": "1.0.0",
        "status": "running",
    }


def test_health_endpoint():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
