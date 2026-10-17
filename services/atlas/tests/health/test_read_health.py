from fastapi.testclient import TestClient


def test_read_health_api_returns_ok_status(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
