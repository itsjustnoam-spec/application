import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import AssetStatus
from atlas.managers.assets import read_asset, update_asset
from atlas.managers.errors import DuplicateSerialNumberError, EntityNotFoundError
from tests.assets.utils import build_asset_body, build_asset_input
from tests.utils import Environment, get_persisted_id

MISSING_ASSET_ID = 9999
MISSING_SITE_ID = 9999


def test_update_asset_valid_input_replaces_editable_fields(
    db_session: Session,
    env: Environment,
):
    asset_id = get_persisted_id(env.compressor)
    asset_input = build_asset_input(
        get_persisted_id(env.south_site),
        get_persisted_id(env.pump),
        name="Pump",
        serial_number=env.compressor.serial_number,
        status=AssetStatus.NEEDS_ATTENTION,
    )

    update_asset(db_session, asset_id, asset_input)
    updated_asset = read_asset(db_session, asset_id)

    assert updated_asset.name == "Pump"
    assert updated_asset.site_name == env.south_site.name
    assert updated_asset.status == AssetStatus.NEEDS_ATTENTION


def test_update_asset_missing_id_raises_entity_not_found_error(
    db_session: Session,
    env: Environment,
):
    asset_input = build_asset_input(
        get_persisted_id(env.north_site),
        get_persisted_id(env.pump),
    )

    with pytest.raises(EntityNotFoundError, match="Asset not found"):
        update_asset(db_session, MISSING_ASSET_ID, asset_input)


def test_update_asset_duplicate_serial_raises_duplicate_serial_number_error(
    db_session: Session,
    env: Environment,
):
    generator_id = get_persisted_id(env.generator)
    asset_input = build_asset_input(
        get_persisted_id(env.south_site),
        get_persisted_id(env.pump),
        serial_number=env.compressor.serial_number,
    )

    with pytest.raises(
        DuplicateSerialNumberError,
        match="An asset with this serial number already exists",
    ):
        update_asset(db_session, generator_id, asset_input)

    assert read_asset(db_session, generator_id).serial_number == "SN-2"


def test_update_asset_keeping_own_serial_number_succeeds(
    db_session: Session,
    env: Environment,
):
    asset_input = build_asset_input(
        get_persisted_id(env.north_site),
        get_persisted_id(env.pump),
        name="Renamed",
        serial_number=env.compressor.serial_number,
    )

    updated_asset = update_asset(db_session, get_persisted_id(env.compressor), asset_input)

    assert updated_asset.serial_number == "SN-1"
    assert updated_asset.name == "Renamed"


def test_update_asset_archived_asset_type_raises_entity_not_found_error(
    db_session: Session,
    env: Environment,
):
    asset_id = get_persisted_id(env.compressor)
    asset_input = build_asset_input(
        get_persisted_id(env.north_site),
        get_persisted_id(env.archived_asset_type),
        serial_number=env.compressor.serial_number,
    )

    with pytest.raises(EntityNotFoundError, match="Asset type not found"):
        update_asset(db_session, asset_id, asset_input)

    assert read_asset(db_session, asset_id).asset_type_id == get_persisted_id(env.pump)


def test_update_asset_missing_site_raises_entity_not_found_error(
    db_session: Session,
    env: Environment,
):
    asset_id = get_persisted_id(env.compressor)
    asset_input = build_asset_input(
        MISSING_SITE_ID,
        get_persisted_id(env.pump),
        serial_number=env.compressor.serial_number,
    )

    with pytest.raises(EntityNotFoundError, match="Site not found"):
        update_asset(db_session, asset_id, asset_input)

    assert read_asset(db_session, asset_id).site_id == get_persisted_id(env.north_site)


def test_update_asset_api_valid_body_returns_200(
    api_client: TestClient,
    env: Environment,
):
    body = build_asset_body(
        get_persisted_id(env.north_site),
        get_persisted_id(env.pump),
        name="Pump",
        serial_number="SN-200",
    )

    response = api_client.put(f"/assets/{get_persisted_id(env.compressor)}", json=body)

    assert response.status_code == 200
    assert response.json()["name"] == "Pump"
    assert response.json()["serial_number"] == "SN-200"


def test_update_asset_api_duplicate_serial_returns_409(
    api_client: TestClient,
    env: Environment,
):
    body = build_asset_body(
        get_persisted_id(env.south_site),
        get_persisted_id(env.pump),
        serial_number=env.compressor.serial_number,
    )

    response = api_client.put(f"/assets/{get_persisted_id(env.generator)}", json=body)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "An asset with this serial number already exists",
    }


def test_update_asset_api_missing_id_returns_404(
    api_client: TestClient,
    env: Environment,
):
    body = build_asset_body(
        get_persisted_id(env.north_site),
        get_persisted_id(env.pump),
    )

    response = api_client.put(f"/assets/{MISSING_ASSET_ID}", json=body)

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}


def test_update_asset_api_missing_site_returns_404(
    api_client: TestClient,
    env: Environment,
):
    body = build_asset_body(MISSING_SITE_ID, get_persisted_id(env.pump))

    response = api_client.put(f"/assets/{get_persisted_id(env.compressor)}", json=body)

    assert response.status_code == 404
    assert response.json() == {"detail": "Site not found"}
