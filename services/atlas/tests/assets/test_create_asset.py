from collections.abc import Callable
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, col, select

from atlas.entities import Asset, AssetStatus, AssetType, Site
from atlas.managers.assets import create_asset, read_asset
from atlas.managers.errors import DuplicateSerialNumberError, EntityNotFoundError
from atlas.schemas.asset import AssetInput
from tests.assets.utils import build_asset_body, count_assets
from tests.utils import get_persisted_id


def test_create_asset_valid_input_persists_asset_with_due_date(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
):
    site = make_site()
    asset_type = make_asset_type(inspection_interval_days=30)
    asset_input = AssetInput(
        name="Compressor",
        serial_number="SN-1",
        site_id=get_persisted_id(site),
        asset_type_id=get_persisted_id(asset_type),
        status=AssetStatus.OPERATIONAL,
        installation_date=date(2026, 1, 1),
    )

    created_asset = create_asset(db_session, asset_input)

    stored_asset = read_asset(db_session, created_asset.id)
    assert stored_asset.name == "Compressor"
    assert stored_asset.archived is False
    assert stored_asset.next_inspection_due == date(2026, 1, 31)


def test_create_asset_duplicate_serial_raises_duplicate_serial_number_error(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type()
    make_asset(site=site, asset_type=asset_type, serial_number="SN-1")
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
        create_asset(db_session, asset_input)

    assert count_assets(db_session) == 1


def test_create_asset_serial_of_archived_asset_succeeds(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type()
    make_asset(site=site, asset_type=asset_type, serial_number="SN-1", archived=True)
    asset_input = AssetInput(
        name="Pump",
        serial_number="SN-1",
        site_id=get_persisted_id(site),
        asset_type_id=get_persisted_id(asset_type),
        status=AssetStatus.OPERATIONAL,
        installation_date=date(2026, 1, 1),
    )

    created_asset = create_asset(db_session, asset_input)

    serial_rows = db_session.exec(
        select(Asset).where(col(Asset.serial_number) == "SN-1"),
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
    make_asset_type: Callable[..., AssetType],
):
    asset_type = make_asset_type()
    asset_input = AssetInput(
        name="Pump",
        serial_number="SN-1",
        site_id=9999,
        asset_type_id=get_persisted_id(asset_type),
        status=AssetStatus.OPERATIONAL,
        installation_date=date(2026, 1, 1),
    )

    with pytest.raises(EntityNotFoundError, match="Site not found"):
        create_asset(db_session, asset_input)

    assert count_assets(db_session) == 0


def test_create_asset_archived_asset_type_raises_entity_not_found_error(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
):
    site = make_site()
    asset_type = make_asset_type(archived=True)
    asset_input = AssetInput(
        name="Pump",
        serial_number="SN-1",
        site_id=get_persisted_id(site),
        asset_type_id=get_persisted_id(asset_type),
        status=AssetStatus.OPERATIONAL,
        installation_date=date(2026, 1, 1),
    )

    with pytest.raises(EntityNotFoundError, match="Asset type not found"):
        create_asset(db_session, asset_input)

    assert count_assets(db_session) == 0


def test_create_asset_future_installation_date_is_accepted(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
):
    site = make_site()
    asset_type = make_asset_type(inspection_interval_days=30)
    asset_input = AssetInput(
        name="Pump",
        serial_number="SN-1",
        site_id=get_persisted_id(site),
        asset_type_id=get_persisted_id(asset_type),
        status=AssetStatus.OPERATIONAL,
        installation_date=date(2999, 1, 1),
    )

    created_asset = create_asset(db_session, asset_input)

    assert created_asset.is_overdue is False


def test_create_asset_api_valid_body_returns_201_with_asset(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
):
    site = make_site(name="North Depot", timezone="Europe/Berlin")
    asset_type = make_asset_type(name="Pump", inspection_interval_days=30)
    body = build_asset_body(get_persisted_id(site), get_persisted_id(asset_type))

    response = api_client.post("/assets", json=body)

    assert response.status_code == 201
    assert response.json() == {
        "id": response.json()["id"],
        "name": "Compressor",
        "serial_number": "SN-1",
        "site_id": get_persisted_id(site),
        "site_name": "North Depot",
        "site_timezone": "Europe/Berlin",
        "asset_type_id": get_persisted_id(asset_type),
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
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    asset_type = make_asset_type()
    make_asset(site=site, asset_type=asset_type, serial_number="SN-1")
    body = build_asset_body(get_persisted_id(site), get_persisted_id(asset_type))

    response = api_client.post("/assets", json=body)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "An asset with this serial number already exists",
    }


def test_create_asset_api_missing_site_returns_404(
    api_client: TestClient,
    make_asset_type: Callable[..., AssetType],
):
    asset_type = make_asset_type()
    body = build_asset_body(9999, get_persisted_id(asset_type))

    response = api_client.post("/assets", json=body)

    assert response.status_code == 404
    assert response.json() == {"detail": "Site not found"}


def test_create_asset_api_archived_asset_type_returns_404(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
):
    site = make_site()
    asset_type = make_asset_type(archived=True)
    body = build_asset_body(get_persisted_id(site), get_persisted_id(asset_type))

    response = api_client.post("/assets", json=body)

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset type not found"}


def test_create_asset_api_blank_notes_saves_notes_as_null(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
):
    site = make_site()
    asset_type = make_asset_type()
    body = build_asset_body(get_persisted_id(site), get_persisted_id(asset_type), notes="   ")

    response = api_client.post("/assets", json=body)

    assert response.status_code == 201
    assert response.json()["notes"] is None


def test_create_asset_api_notes_are_stored_trimmed(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
):
    site = make_site()
    asset_type = make_asset_type()
    body = build_asset_body(
        get_persisted_id(site),
        get_persisted_id(asset_type),
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
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    field_name: str,
    invalid_value: object,
):
    site = make_site()
    asset_type = make_asset_type()
    body = build_asset_body(
        get_persisted_id(site),
        get_persisted_id(asset_type),
        **{field_name: invalid_value},
    )

    response = api_client.post("/assets", json=body)

    assert response.status_code == 422
