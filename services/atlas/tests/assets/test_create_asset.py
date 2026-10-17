from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, col, select

from atlas.entities import Asset
from atlas.managers.assets import create_asset, read_asset
from atlas.managers.errors import DuplicateSerialNumberError, EntityNotFoundError
from tests.assets.utils import (
    NEW_SERIAL_NUMBER,
    build_asset_body,
    build_asset_input,
    count_assets,
)
from tests.utils import Environment, get_persisted_id

MISSING_SITE_ID = 9999


def test_create_asset_valid_input_persists_asset_with_due_date(
    db_session: Session,
    env: Environment,
):
    asset_input = build_asset_input(
        get_persisted_id(env.north_site),
        get_persisted_id(env.pump),
    )

    created_asset = create_asset(db_session, asset_input)

    stored_asset = read_asset(db_session, created_asset.id)
    assert stored_asset.name == "Compressor"
    assert stored_asset.archived is False
    assert stored_asset.next_inspection_due == date(2026, 1, 31)


def test_create_asset_duplicate_serial_raises_duplicate_serial_number_error(
    db_session: Session,
    env: Environment,
):
    asset_input = build_asset_input(
        get_persisted_id(env.north_site),
        get_persisted_id(env.pump),
        serial_number=env.compressor.serial_number,
    )

    with pytest.raises(
        DuplicateSerialNumberError,
        match="An asset with this serial number already exists",
    ):
        create_asset(db_session, asset_input)

    assert count_assets(db_session) == 4


def test_create_asset_serial_of_archived_asset_succeeds(
    db_session: Session,
    env: Environment,
):
    archived_serial_number = env.archived_boiler.serial_number
    asset_input = build_asset_input(
        get_persisted_id(env.north_site),
        get_persisted_id(env.pump),
        serial_number=archived_serial_number,
    )

    created_asset = create_asset(db_session, asset_input)

    serial_rows = db_session.exec(
        select(Asset).where(col(Asset.serial_number) == archived_serial_number),
    ).all()
    archived_rows = [
        row
        for row in serial_rows
        if row.archived
    ]
    assert created_asset.archived is False
    assert len(serial_rows) == 2
    assert len(archived_rows) == 1


def test_create_asset_missing_site_raises_entity_not_found_error(
    db_session: Session,
    env: Environment,
):
    asset_input = build_asset_input(MISSING_SITE_ID, get_persisted_id(env.pump))

    with pytest.raises(EntityNotFoundError, match="Site not found"):
        create_asset(db_session, asset_input)

    assert count_assets(db_session) == 4


def test_create_asset_archived_asset_type_raises_entity_not_found_error(
    db_session: Session,
    env: Environment,
):
    asset_input = build_asset_input(
        get_persisted_id(env.north_site),
        get_persisted_id(env.archived_asset_type),
    )

    with pytest.raises(EntityNotFoundError, match="Asset type not found"):
        create_asset(db_session, asset_input)

    assert count_assets(db_session) == 4


def test_create_asset_future_installation_date_is_accepted(
    db_session: Session,
    env: Environment,
):
    asset_input = build_asset_input(
        get_persisted_id(env.north_site),
        get_persisted_id(env.pump),
        installation_date="2999-01-01",
    )

    created_asset = create_asset(db_session, asset_input)

    assert created_asset.is_overdue is False


def test_create_asset_api_valid_body_returns_201_with_asset(
    api_client: TestClient,
    env: Environment,
):
    site_id = get_persisted_id(env.north_site)
    asset_type_id = get_persisted_id(env.pump)
    body = build_asset_body(site_id, asset_type_id)

    response = api_client.post("/assets", json=body)

    assert response.status_code == 201
    assert response.json() == {
        "id": response.json()["id"],
        "name": "Compressor",
        "serial_number": NEW_SERIAL_NUMBER,
        "site_id": site_id,
        "site_name": "North Depot",
        "site_timezone": "Europe/Berlin",
        "asset_type_id": asset_type_id,
        "asset_type_name": "Pump",
        "status": "Operational",
        "installation_date": "2026-01-01",
        "notes": None,
        "next_inspection_due": "2026-01-31",
        "is_overdue": True,
        "archived": False,
    }


def test_create_asset_api_duplicate_serial_returns_409(
    api_client: TestClient,
    env: Environment,
):
    body = build_asset_body(
        get_persisted_id(env.north_site),
        get_persisted_id(env.pump),
        serial_number=env.compressor.serial_number,
    )

    response = api_client.post("/assets", json=body)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "An asset with this serial number already exists",
    }


def test_create_asset_api_missing_site_returns_404(
    api_client: TestClient,
    env: Environment,
):
    body = build_asset_body(MISSING_SITE_ID, get_persisted_id(env.pump))

    response = api_client.post("/assets", json=body)

    assert response.status_code == 404
    assert response.json() == {"detail": "Site not found"}


def test_create_asset_api_archived_asset_type_returns_404(
    api_client: TestClient,
    env: Environment,
):
    body = build_asset_body(
        get_persisted_id(env.north_site),
        get_persisted_id(env.archived_asset_type),
    )

    response = api_client.post("/assets", json=body)

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset type not found"}


def test_create_asset_api_blank_notes_saves_notes_as_null(
    api_client: TestClient,
    env: Environment,
):
    body = build_asset_body(
        get_persisted_id(env.north_site),
        get_persisted_id(env.pump),
        notes="   ",
    )

    response = api_client.post("/assets", json=body)

    assert response.status_code == 201
    assert response.json()["notes"] is None


def test_create_asset_api_notes_are_stored_trimmed(
    api_client: TestClient,
    env: Environment,
):
    body = build_asset_body(
        get_persisted_id(env.north_site),
        get_persisted_id(env.pump),
        notes="  Check the belt  ",
    )

    response = api_client.post("/assets", json=body)

    assert response.status_code == 201
    assert response.json()["notes"] == "Check the belt"


@pytest.mark.parametrize("field_name,invalid_value", [
    ("name", "   "),
    ("serial_number", "x" * 101),
    ("status", "Broken"),
    ("notes", "x" * 1001),
    ("installation_date", None),
])
def test_create_asset_api_invalid_body_returns_422(
    api_client: TestClient,
    env: Environment,
    field_name: str,
    invalid_value: object,
):
    body = build_asset_body(
        get_persisted_id(env.north_site),
        get_persisted_id(env.pump),
        **{field_name: invalid_value},
    )

    response = api_client.post("/assets", json=body)

    assert response.status_code == 422
