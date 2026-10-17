from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import Site
from atlas.managers.errors import DuplicateNameError
from atlas.managers.sites import create_site, read_site
from atlas.schemas.site import SiteInput
from tests.utils import get_persisted_id

SITE_PAYLOAD = {
    "name": "HQ",
    "address": "1 Main Street",
    "timezone": "Europe/Berlin",
}


def test_create_site_new_name_stores_the_site(db_session: Session):
    site_input = SiteInput(
        name="HQ",
        address="1 Main Street",
        timezone="Europe/Berlin",
    )

    created_site = create_site(db_session, site_input)

    stored_site = read_site(db_session, get_persisted_id(created_site))
    assert stored_site.name == "HQ"


def test_create_site_duplicate_active_name_raises_duplicate_name_error(
    db_session: Session,
    make_site: Callable[..., Site],
):
    make_site(name="HQ")
    site_input = SiteInput(name="HQ", address="2 Side Road", timezone="UTC")

    with pytest.raises(
        DuplicateNameError,
        match="A site with this name already exists",
    ):
        create_site(db_session, site_input)


def test_create_site_archived_name_is_reusable(
    db_session: Session,
    make_site: Callable[..., Site],
):
    make_site(name="HQ", archived=True)
    site_input = SiteInput(name="HQ", address="2 Side Road", timezone="UTC")

    created_site = create_site(db_session, site_input)

    assert created_site.archived is False


def test_create_site_api_valid_body_returns_201_with_site(
    api_client: TestClient,
):
    response = api_client.post("/sites", json=SITE_PAYLOAD)

    assert response.status_code == 201
    assert response.json() == {
        **SITE_PAYLOAD,
        "id": response.json()["id"],
        "archived": False,
    }


def test_create_site_api_duplicate_name_returns_409_with_detail(
    api_client: TestClient,
    make_site: Callable[..., Site],
):
    make_site(name="HQ")

    response = api_client.post("/sites", json=SITE_PAYLOAD)

    assert response.status_code == 409
    assert response.json() == {"detail": "A site with this name already exists"}


def test_create_site_api_unknown_timezone_returns_422_with_reason(
    api_client: TestClient,
):
    body = {**SITE_PAYLOAD, "timezone": "Mars/Olympus"}

    response = api_client.post("/sites", json=body)

    assert response.status_code == 422
    assert "Mars/Olympus is not a valid IANA timezone." in response.text


@pytest.mark.parametrize("field_name,blank_value", [
    ("name", ""),
    ("name", "   "),
    ("address", ""),
])
def test_create_site_api_blank_field_returns_422(
    api_client: TestClient,
    field_name: str,
    blank_value: str,
):
    body = {**SITE_PAYLOAD, field_name: blank_value}

    response = api_client.post("/sites", json=body)

    assert response.status_code == 422
