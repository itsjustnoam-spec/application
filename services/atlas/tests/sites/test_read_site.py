import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.managers.errors import EntityNotFoundError
from atlas.managers.sites import read_site
from tests.utils import Environment, get_persisted_id

MISSING_SITE_ID = 9999


def test_read_site_missing_id_raises_entity_not_found_error(
    db_session: Session,
):
    with pytest.raises(EntityNotFoundError, match="Site not found"):
        read_site(db_session, MISSING_SITE_ID)


def test_read_site_archived_site_raises_entity_not_found_error(
    db_session: Session,
    env: Environment,
):
    site_id = get_persisted_id(env.archived_site)

    with pytest.raises(EntityNotFoundError, match="Site not found"):
        read_site(db_session, site_id)


def test_read_site_api_existing_id_returns_200_with_site(
    api_client: TestClient,
    env: Environment,
):
    response = api_client.get(f"/sites/{get_persisted_id(env.north_site)}")

    assert response.status_code == 200
    assert response.json()["name"] == "North Depot"


def test_read_site_api_missing_id_returns_404_with_detail(
    api_client: TestClient,
):
    response = api_client.get(f"/sites/{MISSING_SITE_ID}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Site not found"}
