"""
API tests for the site endpoints through the FastAPI test client.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from collections.abc import Callable

from fastapi.testclient import TestClient

from atlas.entities import Site

MISSING_SITE_ID = 9999
SITE_PAYLOAD = {
    "name": "HQ",
    "address": "1 Main Street",
    "timezone": "Europe/Berlin",
}


def test_list_sites_returns_page_envelope(
    api_client: TestClient,
    make_site: Callable[..., Site],
):
    make_site(name="HQ")

    response = api_client.get("/sites")

    assert response.status_code == 200
    assert set(response.json().keys()) == {"items", "total", "limit", "offset"}


def test_list_sites_limit_above_100_returns_422(api_client: TestClient):
    response = api_client.get("/sites", params={"limit": 101})

    assert response.status_code == 422


def test_create_site_valid_body_returns_201_with_site(api_client: TestClient):
    response = api_client.post("/sites", json=SITE_PAYLOAD)

    assert response.status_code == 201
    assert response.json()["name"] == "HQ"


def test_create_site_duplicate_name_returns_409_with_detail(
    api_client: TestClient,
    make_site: Callable[..., Site],
):
    make_site(name="HQ")

    response = api_client.post("/sites", json=SITE_PAYLOAD)

    assert response.status_code == 409
    assert response.json() == {"detail": "A site with this name already exists"}


def test_create_site_unknown_timezone_returns_422(api_client: TestClient):
    response = api_client.post(
        "/sites",
        json={**SITE_PAYLOAD, "timezone": "Mars/Olympus"},
    )

    assert response.status_code == 422
    assert "is not a valid IANA timezone" in response.text


def test_get_site_existing_id_returns_200_with_site(
    api_client: TestClient,
    make_site: Callable[..., Site],
):
    site = make_site(name="HQ")

    response = api_client.get(f"/sites/{site.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "HQ"


def test_get_site_missing_id_returns_404_with_detail(api_client: TestClient):
    response = api_client.get(f"/sites/{MISSING_SITE_ID}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Site not found"}


def test_put_site_valid_body_returns_200_with_updated_site(
    api_client: TestClient,
    make_site: Callable[..., Site],
):
    site = make_site(name="HQ")

    response = api_client.put(
        f"/sites/{site.id}",
        json={**SITE_PAYLOAD, "name": "Renamed"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


def test_delete_site_returns_204_and_later_get_returns_404(
    api_client: TestClient,
    make_site: Callable[..., Site],
):
    site = make_site(name="HQ")

    delete_response = api_client.delete(f"/sites/{site.id}")
    get_response = api_client.get(f"/sites/{site.id}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_delete_site_missing_id_returns_404(api_client: TestClient):
    response = api_client.delete(f"/sites/{MISSING_SITE_ID}")

    assert response.status_code == 404
