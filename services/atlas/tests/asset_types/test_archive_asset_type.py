from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import Asset, AssetType, Site
from atlas.managers.asset_types import archive_asset_type, read_asset_type
from atlas.managers.errors import EntityInUseError, EntityNotFoundError
from tests.utils import get_persisted_id

MISSING_ASSET_TYPE_ID = 9999


def test_archive_asset_type_existing_asset_type_hides_it(
    db_session: Session,
    make_asset_type: Callable[..., AssetType],
):
    asset_type_id = get_persisted_id(make_asset_type())

    archive_asset_type(db_session, asset_type_id)

    with pytest.raises(EntityNotFoundError, match="Asset type not found"):
        read_asset_type(db_session, asset_type_id)


def test_archive_asset_type_missing_id_raises_entity_not_found_error(
    db_session: Session,
):
    with pytest.raises(EntityNotFoundError, match="Asset type not found"):
        archive_asset_type(db_session, MISSING_ASSET_TYPE_ID)


def test_archive_asset_type_api_existing_asset_type_returns_204_then_404(
    api_client: TestClient,
    make_asset_type: Callable[..., AssetType],
):
    asset_type_id = get_persisted_id(make_asset_type(name="Pump"))

    delete_response = api_client.delete(f"/asset-types/{asset_type_id}")
    read_response = api_client.get(f"/asset-types/{asset_type_id}")

    assert delete_response.status_code == 204
    assert read_response.status_code == 404


def test_archive_asset_type_with_active_asset_raises_entity_in_use_error(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    asset_type = make_asset_type()
    make_asset(site=make_site(), asset_type=asset_type)

    with pytest.raises(EntityInUseError, match="Asset type has active assets"):
        archive_asset_type(db_session, get_persisted_id(asset_type))

    assert read_asset_type(db_session, get_persisted_id(asset_type)).archived is False


def test_archive_asset_type_with_only_archived_assets_succeeds(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    asset_type = make_asset_type()
    make_asset(site=make_site(), asset_type=asset_type, archived=True)

    archive_asset_type(db_session, get_persisted_id(asset_type))

    with pytest.raises(EntityNotFoundError, match="Asset type not found"):
        read_asset_type(db_session, get_persisted_id(asset_type))


def test_archive_asset_type_api_with_active_asset_returns_409(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    asset_type = make_asset_type()
    make_asset(site=make_site(), asset_type=asset_type)

    response = api_client.delete(f"/asset-types/{get_persisted_id(asset_type)}")

    assert response.status_code == 409
    assert response.json() == {"detail": "Asset type has active assets"}
