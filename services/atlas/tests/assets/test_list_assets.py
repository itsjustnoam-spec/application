from collections.abc import Callable
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import Asset, AssetStatus, AssetType, Site
from atlas.schemas.asset import AssetSort, SortDirection
from tests.assets.utils import list_page, names_of, values_of
from tests.utils import get_persisted_id


def test_list_assets_archived_assets_are_hidden(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type()
    make_asset(site=site, asset_type=asset_type, name="Active", serial_number="S-1")
    make_asset(site=site, asset_type=asset_type, name="Old", serial_number="S-2", archived=True)

    assets, total = list_page(db_session)

    assert names_of(assets) == ["Active"]
    assert total == 1


def test_list_assets_query_matches_name_or_serial_number(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type()
    make_asset(site=site, asset_type=asset_type, name="Compressor", serial_number="ABC-9")
    make_asset(site=site, asset_type=asset_type, name="Pump ABC", serial_number="ZZZ-1")
    make_asset(site=site, asset_type=asset_type, name="Valve", serial_number="DEF-2")

    assets, _ = list_page(db_session, query="abc")

    assert names_of(assets) == ["Compressor", "Pump ABC"]


def test_list_assets_query_treats_percent_as_literal_text(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type()
    make_asset(site=site, asset_type=asset_type, name="Compressor", serial_number="ABC-9")

    assets, total = list_page(db_session, query="%")

    assert names_of(assets) == []
    assert total == 0


def test_list_assets_filters_by_site_asset_type_and_status_together(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    north = make_site(name="North")
    south = make_site(name="South")
    pump = make_asset_type(name="Pump")
    valve = make_asset_type(name="Valve")
    make_asset(site=north, asset_type=pump, name="A", serial_number="S-1")
    make_asset(site=north, asset_type=valve, name="B", serial_number="S-2")
    make_asset(
        site=north,
        asset_type=pump,
        name="C",
        serial_number="S-3",
        status=AssetStatus.RETIRED,
    )
    make_asset(site=south, asset_type=pump, name="D", serial_number="S-4")

    at_site, _ = list_page(db_session, site_id=get_persisted_id(north))
    of_type, _ = list_page(db_session, asset_type_id=get_persisted_id(valve))
    with_status, _ = list_page(db_session, status=AssetStatus.RETIRED)
    combined, _ = list_page(
        db_session,
        site_id=get_persisted_id(north),
        asset_type_id=get_persisted_id(pump),
        status=AssetStatus.OPERATIONAL,
    )

    assert names_of(at_site) == ["A", "B", "C"]
    assert names_of(of_type) == ["B"]
    assert names_of(with_status) == ["C"]
    assert names_of(combined) == ["A"]


def test_list_assets_sort_by_next_due_puts_out_of_service_assets_last(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type(inspection_interval_days=30)
    make_asset(
        site=site,
        asset_type=asset_type,
        name="Later",
        serial_number="S-1",
        installation_date=date(2026, 3, 1),
    )
    make_asset(
        site=site,
        asset_type=asset_type,
        name="Earlier",
        serial_number="S-2",
        installation_date=date(2026, 1, 1),
    )
    make_asset(
        site=site,
        asset_type=asset_type,
        name="Retired",
        serial_number="S-3",
        status=AssetStatus.RETIRED,
        installation_date=date(2025, 1, 1),
    )

    assets, _ = list_page(db_session, sort=AssetSort.NEXT_INSPECTION_DUE)

    assert names_of(assets) == ["Earlier", "Later", "Retired"]


def test_list_assets_sort_by_name_desc_reverses_order(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type()
    make_asset(site=site, asset_type=asset_type, name="Alpha", serial_number="S-1")
    make_asset(site=site, asset_type=asset_type, name="Beta", serial_number="S-2")
    make_asset(site=site, asset_type=asset_type, name="Gamma", serial_number="S-3")

    assets, _ = list_page(db_session, direction=SortDirection.DESC)

    assert names_of(assets) == ["Gamma", "Beta", "Alpha"]


def test_list_assets_sort_ties_are_broken_by_id_ascending(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type()
    first = make_asset(site=site, asset_type=asset_type, name="Same", serial_number="S-1")
    make_asset(site=site, asset_type=asset_type, name="Same", serial_number="S-2")

    assets, _ = list_page(db_session)

    assert assets[0].id == get_persisted_id(first)


def test_list_assets_paging_returns_page_and_total_before_paging(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type()
    make_asset(site=site, asset_type=asset_type, name="Alpha", serial_number="S-1")
    make_asset(site=site, asset_type=asset_type, name="Beta", serial_number="S-2")
    make_asset(site=site, asset_type=asset_type, name="Gamma", serial_number="S-3")

    assets, total = list_page(db_session, limit=2, offset=2)

    assert names_of(assets) == ["Gamma"]
    assert total == 3


def test_list_assets_api_default_returns_paged_envelope(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    make_asset(site=make_site(), asset_type=make_asset_type(), serial_number="S-1")

    response = api_client.get("/assets")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["limit"] == 20
    assert response.json()["offset"] == 0
    assert len(response.json()["items"]) == 1


def test_list_assets_api_search_and_filters_narrow_results(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    north = make_site(name="North")
    south = make_site(name="South")
    pump = make_asset_type(name="Pump")
    valve = make_asset_type(name="Valve")
    make_asset(site=north, asset_type=pump, name="Compressor", serial_number="S-1")
    make_asset(site=south, asset_type=pump, name="Compressor", serial_number="S-2")
    make_asset(site=north, asset_type=valve, name="Compressor", serial_number="S-3")
    make_asset(site=north, asset_type=pump, name="Pump", serial_number="S-4")

    response = api_client.get(
        "/assets",
        params={
            "q": "compressor",
            "site_id": get_persisted_id(north),
            "asset_type_id": get_persisted_id(pump),
            "status": "Operational",
        },
    )

    assert response.status_code == 200
    assert values_of(response.json()["items"], "serial_number") == ["S-1"]
    assert response.json()["total"] == 1


def test_list_assets_api_sort_by_next_due_desc_orders_results(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type(inspection_interval_days=30)
    make_asset(
        site=site,
        asset_type=asset_type,
        name="Earlier",
        serial_number="S-1",
        installation_date=date(2026, 1, 1),
    )
    make_asset(
        site=site,
        asset_type=asset_type,
        name="Later",
        serial_number="S-2",
        installation_date=date(2026, 3, 1),
    )
    make_asset(
        site=site,
        asset_type=asset_type,
        name="Retired",
        serial_number="S-3",
        status=AssetStatus.RETIRED,
        installation_date=date(2025, 1, 1),
    )

    response = api_client.get(
        "/assets",
        params={"sort": "next_inspection_due", "direction": "desc"},
    )

    assert response.status_code == 200
    assert values_of(response.json()["items"], "name") == ["Later", "Earlier", "Retired"]


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
