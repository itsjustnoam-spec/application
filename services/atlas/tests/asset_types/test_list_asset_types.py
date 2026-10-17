from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.managers.asset_types import list_asset_types
from tests.utils import Environment, get_persisted_id


def test_list_asset_types_archived_rows_are_excluded(
    db_session: Session,
    env: Environment,
):
    asset_types, total = list_asset_types(db_session, 20, 0, None)

    assert [
        asset_type.name
        for asset_type in asset_types
    ] == [
        "Boiler",
        "Fan",
        "Pump",
        "Valve",
    ]
    assert total == 4


def test_list_asset_types_query_matches_name_case_insensitively(
    db_session: Session,
    env: Environment,
):
    asset_types, _ = list_asset_types(db_session, 20, 0, "PUMP")

    assert [
        asset_type.name
        for asset_type in asset_types
    ] == [env.pump.name]


def test_list_asset_types_api_returns_page_with_matching_asset_types(
    api_client: TestClient,
    env: Environment,
):
    response = api_client.get("/asset-types", params={"q": "pump"})

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": get_persisted_id(env.pump),
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
