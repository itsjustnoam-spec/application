from collections.abc import Callable
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import Asset, AssetStatus, AssetType, Site
from atlas.managers.assets import read_asset, update_asset
from atlas.managers.errors import DuplicateSerialNumberError, EntityNotFoundError
from atlas.schemas.asset import AssetInput
from tests.assets.utils import build_asset_body
from tests.utils import get_persisted_id

MISSING_ASSET_ID = 9999
MISSING_SITE_ID = 9999


def test_update_asset_valid_input_replaces_editable_fields(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    original_site = make_site(name="North")
    new_site = make_site(name="South")
    asset_type = make_asset_type()
    asset = make_asset(site=original_site, asset_type=asset_type, name="Compressor")
    asset_input = AssetInput(
        name="Pump",
        serial_number="SN-1",
        site_id=get_persisted_id(new_site),
        asset_type_id=get_persisted_id(asset_type),
        status=AssetStatus.NEEDS_ATTENTION,
        installation_date=date(2026, 1, 1),
    )

    update_asset(db_session, get_persisted_id(asset), asset_input)
    updated_asset = read_asset(db_session, get_persisted_id(asset))

    assert updated_asset.name == "Pump"
    assert updated_asset.site_name == "South"
    assert updated_asset.status == AssetStatus.NEEDS_ATTENTION


def test_update_asset_missing_id_raises_entity_not_found_error(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
):
    site = make_site()
    asset_type = make_asset_type()
    asset_input = AssetInput(
        name="Pump",
        serial_number="SN-1",
        site_id=get_persisted_id(site),
        asset_type_id=get_persisted_id(asset_type),
        status=AssetStatus.OPERATIONAL,
        installation_date=date(2026, 1, 1),
    )

    with pytest.raises(EntityNotFoundError, match="Asset not found"):
        update_asset(db_session, MISSING_ASSET_ID, asset_input)


def test_update_asset_duplicate_serial_raises_duplicate_serial_number_error(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type()
    make_asset(site=site, asset_type=asset_type, serial_number="SN-1")
    other = make_asset(site=site, asset_type=asset_type, serial_number="SN-2")
    asset_input = AssetInput(
        name="Pump",
        serial_number="SN-1",
        site_id=get_persisted_id(site),
        asset_type_id=get_persisted_id(asset_type),
        status=AssetStatus.OPERATIONAL,
        installation_date=date(2026, 1, 1),
    )

    with pytest.raises(
        DuplicateSerialNumberError,
        match="An asset with this serial number already exists",
    ):
        update_asset(db_session, get_persisted_id(other), asset_input)

    assert read_asset(db_session, get_persisted_id(other)).serial_number == "SN-2"


def test_update_asset_keeping_own_serial_number_succeeds(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type()
    asset = make_asset(site=site, asset_type=asset_type, serial_number="SN-1")
    asset_input = AssetInput(
        name="Renamed",
        serial_number="SN-1",
        site_id=get_persisted_id(site),
        asset_type_id=get_persisted_id(asset_type),
        status=AssetStatus.OPERATIONAL,
        installation_date=date(2026, 1, 1),
    )

    updated_asset = update_asset(db_session, get_persisted_id(asset), asset_input)

    assert updated_asset.serial_number == "SN-1"
    assert updated_asset.name == "Renamed"


def test_update_asset_archived_asset_type_raises_entity_not_found_error(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    original_type = make_asset_type()
    asset = make_asset(site=site, asset_type=original_type)
    archived_type = make_asset_type(name="Valve", archived=True)
    asset_input = AssetInput(
        name="Compressor",
        serial_number="SN-1",
        site_id=get_persisted_id(site),
        asset_type_id=get_persisted_id(archived_type),
        status=AssetStatus.OPERATIONAL,
        installation_date=date(2026, 1, 1),
    )

    with pytest.raises(EntityNotFoundError, match="Asset type not found"):
        update_asset(db_session, get_persisted_id(asset), asset_input)

    assert read_asset(db_session, get_persisted_id(asset)).asset_type_id == get_persisted_id(
        original_type,
    )


def test_update_asset_missing_site_raises_entity_not_found_error(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type()
    asset = make_asset(site=site, asset_type=asset_type)
    asset_input = AssetInput(
        name="Compressor",
        serial_number="SN-1",
        site_id=MISSING_SITE_ID,
        asset_type_id=get_persisted_id(asset_type),
        status=AssetStatus.OPERATIONAL,
        installation_date=date(2026, 1, 1),
    )

    with pytest.raises(EntityNotFoundError, match="Site not found"):
        update_asset(db_session, get_persisted_id(asset), asset_input)

    assert read_asset(db_session, get_persisted_id(asset)).site_id == get_persisted_id(site)


def test_update_asset_api_valid_body_returns_200(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type()
    asset = make_asset(site=site, asset_type=asset_type, serial_number="SN-1")
    body = build_asset_body(
        get_persisted_id(site),
        get_persisted_id(asset_type),
        name="Pump",
        serial_number="SN-2",
    )

    response = api_client.put(f"/assets/{get_persisted_id(asset)}", json=body)

    assert response.status_code == 200
    assert response.json()["name"] == "Pump"
    assert response.json()["serial_number"] == "SN-2"


def test_update_asset_api_duplicate_serial_returns_409(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type()
    make_asset(site=site, asset_type=asset_type, serial_number="SN-1")
    other = make_asset(site=site, asset_type=asset_type, serial_number="SN-2")
    body = build_asset_body(
        get_persisted_id(site),
        get_persisted_id(asset_type),
        serial_number="SN-1",
    )

    response = api_client.put(f"/assets/{get_persisted_id(other)}", json=body)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "An asset with this serial number already exists",
    }


def test_update_asset_api_missing_id_returns_404(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
):
    site = make_site()
    asset_type = make_asset_type()
    body = build_asset_body(get_persisted_id(site), get_persisted_id(asset_type))

    response = api_client.put(f"/assets/{MISSING_ASSET_ID}", json=body)

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}


def test_update_asset_api_missing_site_returns_404(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type()
    asset = make_asset(site=site, asset_type=asset_type)
    body = build_asset_body(MISSING_SITE_ID, get_persisted_id(asset_type))

    response = api_client.put(f"/assets/{get_persisted_id(asset)}", json=body)

    assert response.status_code == 404
    assert response.json() == {"detail": "Site not found"}
