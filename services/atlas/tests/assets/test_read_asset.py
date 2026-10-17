from collections.abc import Callable
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import Asset, AssetCategory, AssetStatus, AssetType, Site
from atlas.managers import due_dates
from atlas.managers.asset_types import update_asset_type
from atlas.managers.assets import read_asset
from atlas.managers.errors import EntityNotFoundError
from atlas.managers.sites import update_site
from atlas.schemas.asset_type import AssetTypeInput
from atlas.schemas.site import SiteInput
from tests.assets.utils import FrozenDatetime
from tests.utils import get_persisted_id

MISSING_ASSET_ID = 9999
OVERDUE_LONG_AGO = date(2000, 1, 1)
EARLIEST_TIMEZONE = "Pacific/Pago_Pago"
LATEST_TIMEZONE = "Pacific/Kiritimati"


def test_read_asset_missing_id_raises_entity_not_found_error(
    db_session: Session,
):
    with pytest.raises(EntityNotFoundError, match="Asset not found"):
        read_asset(db_session, MISSING_ASSET_ID)


def test_read_asset_archived_raises_entity_not_found_error(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    asset = make_asset(
        site=make_site(),
        asset_type=make_asset_type(),
        archived=True,
    )

    with pytest.raises(EntityNotFoundError, match="Asset not found"):
        read_asset(db_session, get_persisted_id(asset))


def test_read_asset_retired_asset_has_no_due_date_and_is_not_overdue(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    asset = make_asset(
        site=make_site(),
        asset_type=make_asset_type(),
        status=AssetStatus.RETIRED,
        installation_date=OVERDUE_LONG_AGO,
    )

    asset_out = read_asset(db_session, get_persisted_id(asset))

    assert asset_out.next_inspection_due is None
    assert asset_out.is_overdue is False


def test_read_asset_changed_interval_moves_next_due_date(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    asset_type = make_asset_type(inspection_interval_days=30)
    asset = make_asset(
        site=make_site(),
        asset_type=asset_type,
        installation_date=date(2026, 1, 1),
    )
    update_asset_type(
        db_session,
        get_persisted_id(asset_type),
        AssetTypeInput(
            name=asset_type.name,
            category=AssetCategory.MECHANICAL,
            inspection_interval_days=60,
        ),
    )

    asset_out = read_asset(db_session, get_persisted_id(asset))

    assert asset_out.next_inspection_due == date(2026, 3, 2)


def test_read_asset_after_site_timezone_change_recomputes_overdue(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(due_dates, "datetime", FrozenDatetime)
    site = make_site(timezone=EARLIEST_TIMEZONE)
    asset = make_asset(
        site=site,
        asset_type=make_asset_type(inspection_interval_days=1),
        installation_date=date(2026, 10, 16),
    )
    asset_id = get_persisted_id(asset)
    before_change = read_asset(db_session, asset_id)

    update_site(
        db_session,
        get_persisted_id(site),
        SiteInput(
            name=site.name,
            address=site.address,
            timezone=LATEST_TIMEZONE,
        ),
    )
    after_change = read_asset(db_session, asset_id)

    assert before_change.is_overdue is False
    assert after_change.is_overdue is True


def test_read_asset_api_missing_id_returns_404(
    api_client: TestClient,
):
    response = api_client.get(f"/assets/{MISSING_ASSET_ID}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}


def test_read_asset_api_by_id_returns_due_date_and_overdue_flag(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    asset = make_asset(
        site=make_site(timezone="Europe/Berlin"),
        asset_type=make_asset_type(inspection_interval_days=30),
        installation_date=OVERDUE_LONG_AGO,
    )

    response = api_client.get(f"/assets/{get_persisted_id(asset)}")

    assert response.status_code == 200
    assert response.json()["next_inspection_due"] == "2000-01-31"
    assert response.json()["is_overdue"] is True
