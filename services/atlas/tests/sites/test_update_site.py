from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import Site
from atlas.managers.errors import DuplicateNameError, EntityNotFoundError
from atlas.managers.sites import update_site
from atlas.schemas.site import SiteInput
from tests.utils import get_persisted_id

MISSING_SITE_ID = 9999
SITE_PAYLOAD = {
    "name": "Renamed",
    "address": "9 New Road",
    "timezone": "Asia/Tokyo",
}


def test_update_site_existing_site_replaces_fields(
    db_session: Session,
    make_site: Callable[..., Site],
):
    site_id = get_persisted_id(make_site())
    site_input = SiteInput(**SITE_PAYLOAD)

    updated_site = update_site(db_session, site_id, site_input)

    assert (
        updated_site.name,
        updated_site.address,
        updated_site.timezone,
    ) == ("Renamed", "9 New Road", "Asia/Tokyo")


def test_update_site_rename_to_taken_name_raises_duplicate_name_error(
    db_session: Session,
    make_site: Callable[..., Site],
):
    make_site(name="HQ")
    site_id = get_persisted_id(make_site(name="Depot"))
    site_input = SiteInput(name="HQ", address="2 Side Road", timezone="UTC")

    with pytest.raises(
        DuplicateNameError,
        match="A site with this name already exists",
    ):
        update_site(db_session, site_id, site_input)


def test_update_site_missing_id_raises_entity_not_found_error(
    db_session: Session,
):
    site_input = SiteInput(**SITE_PAYLOAD)

    with pytest.raises(EntityNotFoundError, match="Site not found"):
        update_site(db_session, MISSING_SITE_ID, site_input)


def test_update_site_api_valid_body_returns_200_with_updated_site(
    api_client: TestClient,
    make_site: Callable[..., Site],
):
    site_id = get_persisted_id(make_site(name="HQ"))

    response = api_client.put(f"/sites/{site_id}", json=SITE_PAYLOAD)

    assert response.status_code == 200
    assert response.json() == {
        **SITE_PAYLOAD,
        "id": site_id,
        "archived": False,
    }


def test_update_site_api_taken_name_returns_409_with_detail(
    api_client: TestClient,
    make_site: Callable[..., Site],
):
    make_site(name="HQ")
    site_id = get_persisted_id(make_site(name="Depot"))
    body = {**SITE_PAYLOAD, "name": "HQ"}

    response = api_client.put(f"/sites/{site_id}", json=body)

    assert response.status_code == 409
    assert response.json() == {"detail": "A site with this name already exists"}
