import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import AssetStatus
from atlas.managers.assets import create_asset
from atlas.schemas.asset import AssetSort, SortDirection
from tests.assets.utils import build_asset_input, list_page, names_of, values_of
from tests.utils import Environment, get_persisted_id


def test_list_assets_archived_assets_are_hidden(
    db_session: Session,
    env: Environment,
):
    assets, total = list_page(db_session)

    assert names_of(assets) == [
        "Compressor",
        "Conveyor",
        "Fan",
        "Generator",
    ]
    assert total == 4


def test_list_assets_query_matches_name(
    db_session: Session,
    env: Environment,
):
    assets, _ = list_page(db_session, query="COMP")

    assert names_of(assets) == [env.compressor.name]


def test_list_assets_query_matches_serial_number(
    db_session: Session,
    env: Environment,
):
    assets, _ = list_page(db_session, query="sn-2")

    assert names_of(assets) == [env.generator.name]


def test_list_assets_query_treats_percent_as_literal_text(
    db_session: Session,
    env: Environment,
):
    assets, total = list_page(db_session, query="%")

    assert names_of(assets) == []
    assert total == 0


def test_list_assets_filters_by_site_asset_type_and_status_together(
    db_session: Session,
    env: Environment,
):
    north_site_id = get_persisted_id(env.north_site)

    at_site, _ = list_page(db_session, site_id=north_site_id)
    of_type, _ = list_page(db_session, asset_type_id=get_persisted_id(env.fan))
    with_status, _ = list_page(db_session, status=AssetStatus.RETIRED)
    combined, _ = list_page(
        db_session,
        site_id=north_site_id,
        asset_type_id=get_persisted_id(env.pump),
        status=AssetStatus.OPERATIONAL,
    )

    assert names_of(at_site) == [
        "Compressor",
        "Conveyor",
    ]
    assert names_of(of_type) == [env.island_fan.name]
    assert names_of(with_status) == [env.retired_conveyor.name]
    assert names_of(combined) == [env.compressor.name]


def test_list_assets_sort_by_next_due_puts_assets_without_due_date_last(
    db_session: Session,
    env: Environment,
):
    assets, _ = list_page(db_session, sort=AssetSort.NEXT_INSPECTION_DUE)

    assert names_of(assets) == [
        "Compressor",
        "Generator",
        "Fan",
        "Conveyor",
    ]


def test_list_assets_sort_by_name_desc_reverses_order(
    db_session: Session,
    env: Environment,
):
    assets, _ = list_page(db_session, direction=SortDirection.DESC)

    assert names_of(assets) == [
        "Generator",
        "Fan",
        "Conveyor",
        "Compressor",
    ]


def test_list_assets_sort_ties_are_broken_by_id_ascending(
    db_session: Session,
    env: Environment,
):
    asset_input = build_asset_input(
        get_persisted_id(env.south_site),
        get_persisted_id(env.pump),
        name=env.compressor.name,
    )
    create_asset(db_session, asset_input)

    assets, _ = list_page(db_session, query=env.compressor.name)

    assert [
        asset.serial_number
        for asset in assets
    ] == [
        "SN-1",
        "SN-100",
    ]


def test_list_assets_paging_returns_page_and_total_before_paging(
    db_session: Session,
    env: Environment,
):
    assets, total = list_page(db_session, limit=2, offset=2)

    assert names_of(assets) == [
        "Fan",
        "Generator",
    ]
    assert total == 4


def test_list_assets_api_default_returns_paged_envelope(
    api_client: TestClient,
    env: Environment,
):
    response = api_client.get("/assets")

    assert response.status_code == 200
    assert response.json()["total"] == 4
    assert response.json()["limit"] == 20
    assert response.json()["offset"] == 0
    assert len(response.json()["items"]) == 4


def test_list_assets_api_search_and_filters_narrow_results(
    api_client: TestClient,
    env: Environment,
):
    response = api_client.get(
        "/assets",
        params={
            "q": "c",
            "site_id": get_persisted_id(env.north_site),
            "asset_type_id": get_persisted_id(env.pump),
            "status": "Operational",
        },
    )

    assert response.status_code == 200
    assert values_of(response.json()["items"], "serial_number") == ["SN-1"]
    assert response.json()["total"] == 1


def test_list_assets_api_sort_by_next_due_desc_orders_results(
    api_client: TestClient,
    env: Environment,
):
    response = api_client.get(
        "/assets",
        params={"sort": "next_inspection_due", "direction": "desc"},
    )

    assert response.status_code == 200
    assert values_of(response.json()["items"], "name") == [
        "Fan",
        "Generator",
        "Compressor",
        "Conveyor",
    ]


@pytest.mark.parametrize("params", [
    {"limit": 101},
    {"offset": -1},
    {"q": "x" * 101},
    {"sort": "color"},
    {"direction": "up"},
])
def test_list_assets_api_invalid_query_params_return_422(
    api_client: TestClient,
    params: dict[str, object],
):
    response = api_client.get("/assets", params=params)

    assert response.status_code == 422
