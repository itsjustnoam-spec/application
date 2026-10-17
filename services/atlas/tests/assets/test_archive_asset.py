from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import Asset, AssetType, Site
from atlas.managers.assets import archive_asset, read_asset
from atlas.managers.errors import EntityNotFoundError
from tests.utils import get_persisted_id

MISSING_ASSET_ID = 9999


def test_archive_asset_sets_archived_flag_and_keeps_row(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    asset = make_asset(site=make_site(), asset_type=make_asset_type())
    asset_id = get_persisted_id(asset)

    archive_asset(db_session, asset_id)

    assert db_session.get(Asset, asset_id).archived is True
    with pytest.raises(EntityNotFoundError, match="Asset not found"):
        read_asset(db_session, asset_id)


def test_archive_asset_missing_id_raises_entity_not_found_error(
    db_session: Session,
):
    with pytest.raises(EntityNotFoundError, match="Asset not found"):
        archive_asset(db_session, MISSING_ASSET_ID)


def test_archive_asset_api_active_id_returns_204_then_404(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    asset = make_asset(site=make_site(), asset_type=make_asset_type())
    asset_id = get_persisted_id(asset)

    delete_response = api_client.delete(f"/assets/{asset_id}")
    read_response = api_client.get(f"/assets/{asset_id}")

    assert delete_response.status_code == 204
    assert read_response.status_code == 404


def test_archive_asset_api_archived_id_returns_404(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    asset = make_asset(site=make_site(), asset_type=make_asset_type(), archived=True)

    response = api_client.delete(f"/assets/{get_persisted_id(asset)}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}
