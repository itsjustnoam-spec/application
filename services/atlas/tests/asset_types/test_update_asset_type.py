import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import AssetCategory
from atlas.managers.asset_types import update_asset_type
from atlas.managers.errors import DuplicateNameError, EntityNotFoundError
from atlas.schemas.asset_type import AssetTypeInput
from tests.utils import Environment, get_persisted_id

MISSING_ASSET_TYPE_ID = 9999
ASSET_TYPE_PAYLOAD = {
    "name": "Compressor",
    "category": "Safety",
    "inspection_interval_days": 90,
}


def test_update_asset_type_existing_asset_type_replaces_fields(
    db_session: Session,
    env: Environment,
):
    asset_type_input = AssetTypeInput.model_validate(ASSET_TYPE_PAYLOAD)

    updated_asset_type = update_asset_type(
        db_session,
        get_persisted_id(env.valve),
        asset_type_input,
    )

    assert (
        updated_asset_type.name,
        updated_asset_type.category,
        updated_asset_type.inspection_interval_days,
    ) == ("Compressor", AssetCategory.SAFETY, 90)


def test_update_asset_type_rename_to_taken_name_raises_duplicate_name_error(
    db_session: Session,
    env: Environment,
):
    asset_type_input = AssetTypeInput(
        name=env.pump.name,
        category=AssetCategory.MECHANICAL,
        inspection_interval_days=30,
    )

    with pytest.raises(
        DuplicateNameError,
        match="An asset type with this name already exists",
    ):
        update_asset_type(
            db_session,
            get_persisted_id(env.valve),
            asset_type_input,
        )


def test_update_asset_type_missing_id_raises_entity_not_found_error(
    db_session: Session,
):
    asset_type_input = AssetTypeInput.model_validate(ASSET_TYPE_PAYLOAD)

    with pytest.raises(EntityNotFoundError, match="Asset type not found"):
        update_asset_type(
            db_session,
            MISSING_ASSET_TYPE_ID,
            asset_type_input,
        )


def test_update_asset_type_api_valid_body_returns_200_with_updated_asset_type(
    api_client: TestClient,
    env: Environment,
):
    asset_type_id = get_persisted_id(env.valve)

    response = api_client.put(
        f"/asset-types/{asset_type_id}",
        json=ASSET_TYPE_PAYLOAD,
    )

    assert response.status_code == 200
    assert response.json() == {
        **ASSET_TYPE_PAYLOAD,
        "id": asset_type_id,
        "archived": False,
    }
