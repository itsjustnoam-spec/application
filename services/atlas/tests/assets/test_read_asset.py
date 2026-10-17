from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.managers import due_dates
from atlas.managers.asset_types import update_asset_type
from atlas.managers.assets import read_asset
from atlas.managers.errors import EntityNotFoundError
from atlas.managers.sites import update_site
from atlas.schemas.asset_type import AssetTypeInput
from atlas.schemas.site import SiteInput
from tests.assets.utils import FrozenDatetime
from tests.utils import LATEST_TIMEZONE, Environment, get_persisted_id

MISSING_ASSET_ID = 9999


def test_read_asset_missing_id_raises_entity_not_found_error(
    db_session: Session,
):
    with pytest.raises(EntityNotFoundError, match="Asset not found"):
        read_asset(db_session, MISSING_ASSET_ID)


def test_read_asset_archived_raises_entity_not_found_error(
    db_session: Session,
    env: Environment,
):
    with pytest.raises(EntityNotFoundError, match="Asset not found"):
        read_asset(db_session, get_persisted_id(env.archived_boiler))


def test_read_asset_retired_asset_has_no_due_date_and_is_not_overdue(
    db_session: Session,
    env: Environment,
):
    asset_out = read_asset(db_session, get_persisted_id(env.retired_conveyor))

    assert asset_out.next_inspection_due is None
    assert asset_out.is_overdue is False


def test_read_asset_changed_interval_moves_next_due_date(
    db_session: Session,
    env: Environment,
):
    update_asset_type(
        db_session,
        get_persisted_id(env.pump),
        AssetTypeInput(
            name=env.pump.name,
            category=env.pump.category,
            inspection_interval_days=60,
        ),
    )

    asset_out = read_asset(db_session, get_persisted_id(env.compressor))

    assert asset_out.next_inspection_due == date(2026, 3, 2)


def test_read_asset_after_site_timezone_change_recomputes_overdue(
    db_session: Session,
    env: Environment,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(due_dates, "datetime", FrozenDatetime)
    asset_id = get_persisted_id(env.island_fan)
    before_change = read_asset(db_session, asset_id)

    update_site(
        db_session,
        get_persisted_id(env.island_site),
        SiteInput(
            name=env.island_site.name,
            address=env.island_site.address,
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
    env: Environment,
):
    response = api_client.get(f"/assets/{get_persisted_id(env.compressor)}")

    assert response.status_code == 200
    assert response.json()["next_inspection_due"] == "2026-01-31"
    assert response.json()["is_overdue"] is True
