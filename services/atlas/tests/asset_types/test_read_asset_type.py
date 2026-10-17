import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.managers.asset_types import read_asset_type
from atlas.managers.errors import EntityNotFoundError
from tests.utils import Environment, get_persisted_id

MISSING_ASSET_TYPE_ID = 9999


def test_read_asset_type_missing_id_raises_entity_not_found_error(
    db_session: Session,
):
    with pytest.raises(EntityNotFoundError, match="Asset type not found"):
        read_asset_type(db_session, MISSING_ASSET_TYPE_ID)


def test_read_asset_type_archived_asset_type_raises_entity_not_found_error(
    db_session: Session,
    env: Environment,
):
    asset_type_id = get_persisted_id(env.archived_asset_type)

    with pytest.raises(EntityNotFoundError, match="Asset type not found"):
        read_asset_type(db_session, asset_type_id)


def test_read_asset_type_api_existing_id_returns_200_with_asset_type(
    api_client: TestClient,
    env: Environment,
):
    response = api_client.get(f"/asset-types/{get_persisted_id(env.pump)}")

    assert response.status_code == 200
    assert response.json()["name"] == "Pump"


def test_read_asset_type_api_missing_id_returns_404_with_detail(
    api_client: TestClient,
):
    response = api_client.get(f"/asset-types/{MISSING_ASSET_TYPE_ID}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset type not found"}
