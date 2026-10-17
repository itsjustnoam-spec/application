from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import Asset, AssetType, Site
from atlas.managers.errors import EntityInUseError, EntityNotFoundError
from atlas.managers.sites import archive_site, list_sites, read_site
from tests.utils import get_persisted_id

MISSING_SITE_ID = 9999


def test_archive_site_existing_site_hides_it(
    db_session: Session,
    make_site: Callable[..., Site],
):
    site_id = get_persisted_id(make_site())

    archive_site(db_session, site_id)

    with pytest.raises(EntityNotFoundError, match="Site not found"):
        read_site(db_session, site_id)


def test_archive_site_existing_site_removes_it_from_list(
    db_session: Session,
    make_site: Callable[..., Site],
):
    site_id = get_persisted_id(make_site())

    archive_site(db_session, site_id)

    assert list_sites(db_session, 20, 0, None) == ([], 0)


def test_archive_site_missing_id_raises_entity_not_found_error(
    db_session: Session,
):
    with pytest.raises(EntityNotFoundError, match="Site not found"):
        archive_site(db_session, MISSING_SITE_ID)


def test_archive_site_api_existing_site_returns_204_then_404(
    api_client: TestClient,
    make_site: Callable[..., Site],
):
    site_id = get_persisted_id(make_site(name="HQ"))

    delete_response = api_client.delete(f"/sites/{site_id}")
    read_response = api_client.get(f"/sites/{site_id}")

    assert delete_response.status_code == 204
    assert read_response.status_code == 404


def test_archive_site_api_missing_id_returns_404_with_detail(
    api_client: TestClient,
):
    response = api_client.delete(f"/sites/{MISSING_SITE_ID}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Site not found"}


def test_archive_site_with_active_asset_raises_entity_in_use_error(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    make_asset(site=site, asset_type=make_asset_type())

    with pytest.raises(EntityInUseError, match="Site has active assets"):
        archive_site(db_session, get_persisted_id(site))

    assert read_site(db_session, get_persisted_id(site)).archived is False


def test_archive_site_with_only_archived_assets_succeeds(
    db_session: Session,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    make_asset(site=site, asset_type=make_asset_type(), archived=True)

    archive_site(db_session, get_persisted_id(site))

    with pytest.raises(EntityNotFoundError, match="Site not found"):
        read_site(db_session, get_persisted_id(site))


def test_archive_site_api_with_active_asset_returns_409(
    api_client: TestClient,
    make_site: Callable[..., Site],
    make_asset_type: Callable[..., AssetType],
    make_asset: Callable[..., Asset],
):
    site = make_site()
    make_asset(site=site, asset_type=make_asset_type())

    response = api_client.delete(f"/sites/{get_persisted_id(site)}")

    assert response.status_code == 409
    assert response.json() == {"detail": "Site has active assets"}
