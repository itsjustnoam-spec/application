from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import AssetType
from atlas.managers.asset_types import archive_asset_type, read_asset_type
from atlas.managers.errors import EntityNotFoundError
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
