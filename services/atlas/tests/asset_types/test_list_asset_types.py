from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import AssetType
from atlas.managers.asset_types import list_asset_types


def test_list_asset_types_archived_rows_are_excluded(
    db_session: Session,
    make_asset_type: Callable[..., AssetType],
):
    make_asset_type(name="Pump")
    make_asset_type(name="Valve", archived=True)

    asset_types, total = list_asset_types(db_session, 20, 0, None)

    assert [
        asset_type.name
        for asset_type in asset_types
    ] == ["Pump"]
    assert total == 1


def test_list_asset_types_query_matches_name_case_insensitively(
    db_session: Session,
    make_asset_type: Callable[..., AssetType],
):
    make_asset_type(name="Pump")
    make_asset_type(name="Valve")

    asset_types, _ = list_asset_types(db_session, 20, 0, "pump")

    assert [
        asset_type.name
        for asset_type in asset_types
    ] == ["Pump"]


def test_list_asset_types_api_returns_page_with_matching_asset_types(
    api_client: TestClient,
    make_asset_type: Callable[..., AssetType],
):
    make_asset_type(name="Pump")
    make_asset_type(name="Valve")

    response = api_client.get("/asset-types", params={"q": "pump"})

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": response.json()["items"][0]["id"],
                "name": "Pump",
                "category": "Mechanical",
                "inspection_interval_days": 30,
                "archived": False,
            },
        ],
        "total": 1,
        "limit": 20,
        "offset": 0,
    }
