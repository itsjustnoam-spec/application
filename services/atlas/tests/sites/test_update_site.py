import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.managers.errors import DuplicateNameError, EntityNotFoundError
from atlas.managers.sites import update_site
from atlas.schemas.site import SiteInput
from tests.utils import Environment, get_persisted_id

MISSING_SITE_ID = 9999
SITE_PAYLOAD = {
    "name": "Renamed",
    "address": "9 New Road",
    "timezone": "Asia/Tokyo",
}


def test_update_site_existing_site_replaces_fields(
    db_session: Session,
    env: Environment,
):
    site_input = SiteInput(**SITE_PAYLOAD)

    updated_site = update_site(db_session, get_persisted_id(env.empty_site), site_input)

    assert (
        updated_site.name,
        updated_site.address,
        updated_site.timezone,
    ) == ("Renamed", "9 New Road", "Asia/Tokyo")


def test_update_site_rename_to_taken_name_raises_duplicate_name_error(
    db_session: Session,
    env: Environment,
):
    site_input = SiteInput(name=env.north_site.name, address="2 Side Road", timezone="UTC")

    with pytest.raises(
        DuplicateNameError,
        match="A site with this name already exists",
    ):
        update_site(db_session, get_persisted_id(env.empty_site), site_input)


def test_update_site_missing_id_raises_entity_not_found_error(
    db_session: Session,
):
    site_input = SiteInput(**SITE_PAYLOAD)

    with pytest.raises(EntityNotFoundError, match="Site not found"):
        update_site(db_session, MISSING_SITE_ID, site_input)


def test_update_site_api_valid_body_returns_200_with_updated_site(
    api_client: TestClient,
    env: Environment,
):
    site_id = get_persisted_id(env.empty_site)

    response = api_client.put(f"/sites/{site_id}", json=SITE_PAYLOAD)

    assert response.status_code == 200
    assert response.json() == {
        **SITE_PAYLOAD,
        "id": site_id,
        "archived": False,
    }


def test_update_site_api_taken_name_returns_409_with_detail(
    api_client: TestClient,
    env: Environment,
):
    body = {**SITE_PAYLOAD, "name": env.north_site.name}

    response = api_client.put(f"/sites/{get_persisted_id(env.empty_site)}", json=body)

    assert response.status_code == 409
    assert response.json() == {"detail": "A site with this name already exists"}
