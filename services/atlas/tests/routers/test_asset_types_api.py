"""
API tests for the asset type endpoints through the FastAPI test client.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from collections.abc import Callable

from fastapi.testclient import TestClient

from atlas.entities import AssetType

MISSING_ASSET_TYPE_ID = 9999
ASSET_TYPE_PAYLOAD = {
    "name": "Pump",
    "category": "Mechanical",
    "inspection_interval_days": 30,
}


def test_list_asset_types_returns_page_envelope(
    api_client: TestClient,
    make_asset_type: Callable[..., AssetType],
):
    make_asset_type(name="Pump")

    response = api_client.get("/asset-types")

    assert response.status_code == 200
    assert set(response.json().keys()) == {"items", "total", "limit", "offset"}


def test_create_asset_type_valid_body_returns_201_with_asset_type(api_client: TestClient):
    response = api_client.post("/asset-types", json=ASSET_TYPE_PAYLOAD)

    assert response.status_code == 201
    assert response.json()["inspection_interval_days"] == 30


def test_create_asset_type_interval_out_of_range_returns_422(api_client: TestClient):
    response = api_client.post(
        "/asset-types",
        json={**ASSET_TYPE_PAYLOAD, "inspection_interval_days": 0},
    )

    assert response.status_code == 422


def test_create_asset_type_unknown_category_returns_422(api_client: TestClient):
    response = api_client.post(
        "/asset-types",
        json={**ASSET_TYPE_PAYLOAD, "category": "Plumbing"},
    )

    assert response.status_code == 422


def test_create_asset_type_duplicate_name_returns_409_with_detail(
    api_client: TestClient,
    make_asset_type: Callable[..., AssetType],
):
    make_asset_type(name="Pump")

    response = api_client.post("/asset-types", json=ASSET_TYPE_PAYLOAD)

    assert response.status_code == 409
    assert response.json() == {"detail": "An asset type with this name already exists"}


def test_get_asset_type_existing_id_returns_200_with_asset_type(
    api_client: TestClient,
    make_asset_type: Callable[..., AssetType],
):
    asset_type = make_asset_type(name="Pump")

    response = api_client.get(f"/asset-types/{asset_type.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Pump"


def test_get_asset_type_missing_id_returns_404_with_detail(api_client: TestClient):
    response = api_client.get(f"/asset-types/{MISSING_ASSET_TYPE_ID}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset type not found"}


def test_put_asset_type_valid_body_returns_200_with_updated_asset_type(
    api_client: TestClient,
    make_asset_type: Callable[..., AssetType],
):
    asset_type = make_asset_type(name="Pump")

    response = api_client.put(
        f"/asset-types/{asset_type.id}",
        json={**ASSET_TYPE_PAYLOAD, "inspection_interval_days": 60},
    )

    assert response.status_code == 200
    assert response.json()["inspection_interval_days"] == 60


def test_delete_asset_type_returns_204_and_later_get_returns_404(
    api_client: TestClient,
    make_asset_type: Callable[..., AssetType],
):
    asset_type = make_asset_type(name="Pump")

    delete_response = api_client.delete(f"/asset-types/{asset_type.id}")
    get_response = api_client.get(f"/asset-types/{asset_type.id}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404
