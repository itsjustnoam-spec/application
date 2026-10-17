import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import AssetCategory
from atlas.managers.asset_types import create_asset_type, read_asset_type
from atlas.managers.errors import DuplicateNameError
from atlas.schemas.asset_type import AssetTypeInput
from tests.utils import Environment, get_persisted_id

ASSET_TYPE_PAYLOAD = {
    "name": "Chiller",
    "category": "HVAC",
    "inspection_interval_days": 30,
}


def test_create_asset_type_new_name_stores_the_asset_type(
    db_session: Session,
):
    asset_type_input = AssetTypeInput(
        name="Chiller",
        category=AssetCategory.HVAC,
        inspection_interval_days=30,
    )

    created_asset_type = create_asset_type(db_session, asset_type_input)

    asset_type_id = get_persisted_id(created_asset_type)
    assert read_asset_type(db_session, asset_type_id).name == "Chiller"


def test_create_asset_type_duplicate_active_name_raises_duplicate_name_error(
    db_session: Session,
    env: Environment,
):
    asset_type_input = AssetTypeInput(
        name=env.pump.name,
        category=AssetCategory.HVAC,
        inspection_interval_days=60,
    )

    with pytest.raises(
        DuplicateNameError,
        match="An asset type with this name already exists",
    ):
        create_asset_type(db_session, asset_type_input)


def test_create_asset_type_archived_name_is_reusable(
    db_session: Session,
    env: Environment,
):
    asset_type_input = AssetTypeInput(
        name=env.archived_asset_type.name,
        category=AssetCategory.HVAC,
        inspection_interval_days=60,
    )

    created_asset_type = create_asset_type(db_session, asset_type_input)

    assert created_asset_type.archived is False


def test_create_asset_type_api_valid_body_returns_201_with_asset_type(
    api_client: TestClient,
):
    response = api_client.post("/asset-types", json=ASSET_TYPE_PAYLOAD)

    assert response.status_code == 201
    assert response.json() == {
        **ASSET_TYPE_PAYLOAD,
        "id": response.json()["id"],
        "archived": False,
    }


def test_create_asset_type_api_duplicate_name_returns_409_with_detail(
    api_client: TestClient,
    env: Environment,
):
    body = {**ASSET_TYPE_PAYLOAD, "name": env.pump.name}

    response = api_client.post("/asset-types", json=body)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "An asset type with this name already exists",
    }


@pytest.mark.parametrize("field_name,invalid_value", [
    ("inspection_interval_days", 0),
    ("inspection_interval_days", 3651),
    ("category", "Plumbing"),
    ("name", "   "),
])
def test_create_asset_type_api_invalid_field_returns_422(
    api_client: TestClient,
    field_name: str,
    invalid_value: object,
):
    body = {**ASSET_TYPE_PAYLOAD, field_name: invalid_value}

    response = api_client.post("/asset-types", json=body)

    assert response.status_code == 422
