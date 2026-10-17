"""
Health endpoint tests for the proxy.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok_status(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
