import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import Asset
from atlas.managers.assets import archive_asset, read_asset
from atlas.managers.errors import EntityNotFoundError
from tests.utils import Environment, get_persisted_id

MISSING_ASSET_ID = 9999


def test_archive_asset_sets_archived_flag_and_keeps_row(
    db_session: Session,
    env: Environment,
):
    asset_id = get_persisted_id(env.compressor)

    archive_asset(db_session, asset_id)

    archived_asset = db_session.get(Asset, asset_id)
    assert archived_asset is not None
    assert archived_asset.archived is True
    with pytest.raises(EntityNotFoundError, match="Asset not found"):
        read_asset(db_session, asset_id)


def test_archive_asset_missing_id_raises_entity_not_found_error(
    db_session: Session,
):
    with pytest.raises(EntityNotFoundError, match="Asset not found"):
        archive_asset(db_session, MISSING_ASSET_ID)


def test_archive_asset_api_active_id_returns_204_then_404(
    api_client: TestClient,
    env: Environment,
):
    asset_id = get_persisted_id(env.compressor)

    delete_response = api_client.delete(f"/assets/{asset_id}")
    read_response = api_client.get(f"/assets/{asset_id}")

    assert delete_response.status_code == 204
    assert read_response.status_code == 404


def test_archive_asset_api_archived_id_returns_404(
    api_client: TestClient,
    env: Environment,
):
    response = api_client.delete(f"/assets/{get_persisted_id(env.archived_boiler)}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}
