"""
Forwarding tests for the proxy's /api/<service>/... route.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from collections.abc import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from juniper.main import SERVICE_BASE_URLS, app, get_http_client

# ----- Functions ----- #


@pytest.fixture
def upstream_requests() -> Iterator[list[httpx.Request]]:
    recorded_requests: list[httpx.Request] = []

    def handle_upstream_request(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json={"items": []})

    upstream_client = httpx.AsyncClient(
        transport=httpx.MockTransport(handle_upstream_request),
    )
    app.dependency_overrides[get_http_client] = lambda: upstream_client
    yield recorded_requests
    app.dependency_overrides.clear()


def test_forward_known_service_relays_upstream_response(
    client: TestClient,
    upstream_requests: list[httpx.Request],
):
    response = client.get("/api/atlas/entities")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_forward_known_service_targets_registered_base_url(
    client: TestClient,
    upstream_requests: list[httpx.Request],
):
    client.get("/api/atlas/entities?page=2")

    assert str(upstream_requests[0].url) == f"{SERVICE_BASE_URLS['atlas']}/entities?page=2"


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_forward_preserves_request_method(
    client: TestClient,
    upstream_requests: list[httpx.Request],
    method: str,
):
    client.request(method, "/api/orion/files")

    assert upstream_requests[0].method == method


def test_forward_unknown_service_returns_not_found(client: TestClient):
    response = client.get("/api/unknown/entities")

    assert response.status_code == 404
    assert response.json() == {"detail": "Service 'unknown' is not registered."}
