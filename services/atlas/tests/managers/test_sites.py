"""
Integration tests for the site manager against the test database.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from collections.abc import Callable

import pytest
from sqlmodel import Session

from atlas.entities import Site
from atlas.managers.errors import DuplicateNameError, EntityNotFoundError
from atlas.managers.sites import (
    archive_site,
    create_site,
    list_sites,
    read_site,
    update_site,
)
from atlas.schemas.site import SiteInput

MISSING_SITE_ID = 9999


def test_list_sites_excludes_archived_rows(
    db_session: Session,
    make_site: Callable[..., Site],
):
    make_site(name="North Depot")
    make_site(name="Old Depot", archived=True)

    sites, total = list_sites(db_session, 20, 0, None)

    assert [site.name for site in sites] == ["North Depot"]
    assert total == 1


def test_list_sites_query_matches_name_case_insensitively(
    db_session: Session,
    make_site: Callable[..., Site],
):
    make_site(name="North Depot")
    make_site(name="South Depot")

    sites, _ = list_sites(db_session, 20, 0, "NORTH")

    assert [site.name for site in sites] == ["North Depot"]


def test_list_sites_limit_and_offset_return_requested_page(
    db_session: Session,
    make_site: Callable[..., Site],
):
    make_site(name="A Depot")
    make_site(name="B Depot")
    make_site(name="C Depot")

    sites, total = list_sites(db_session, 2, 2, None)

    assert [site.name for site in sites] == ["C Depot"]
    assert total == 3


def test_read_site_missing_id_raises_entity_not_found_error(db_session: Session):
    with pytest.raises(EntityNotFoundError, match="Site not found"):
        read_site(db_session, MISSING_SITE_ID)


def test_read_site_archived_id_raises_entity_not_found_error(
    db_session: Session,
    make_site: Callable[..., Site],
):
    archived_site = make_site(archived=True)
    assert archived_site.id is not None

    with pytest.raises(EntityNotFoundError, match="Site not found"):
        read_site(db_session, archived_site.id)


def test_create_site_duplicate_active_name_raises_duplicate_name_error(
    db_session: Session,
    make_site: Callable[..., Site],
):
    make_site(name="HQ")

    with pytest.raises(
        DuplicateNameError,
        match="A site with this name already exists",
    ):
        create_site(
            db_session,
            SiteInput(name="HQ", address="2 Side Road", timezone="UTC"),
        )


def test_create_site_archived_name_is_reusable(
    db_session: Session,
    make_site: Callable[..., Site],
):
    make_site(name="HQ", archived=True)

    created_site = create_site(
        db_session,
        SiteInput(name="HQ", address="2 Side Road", timezone="UTC"),
    )

    assert created_site.archived is False


def test_update_site_rename_to_taken_name_raises_duplicate_name_error(
    db_session: Session,
    make_site: Callable[..., Site],
):
    make_site(name="HQ")
    other_site = make_site(name="Depot")
    assert other_site.id is not None

    with pytest.raises(
        DuplicateNameError,
        match="A site with this name already exists",
    ):
        update_site(
            db_session,
            other_site.id,
            SiteInput(name="HQ", address="2 Side Road", timezone="UTC"),
        )


def test_update_site_replaces_fields(
    db_session: Session,
    make_site: Callable[..., Site],
):
    site = make_site()
    assert site.id is not None

    updated_site = update_site(
        db_session,
        site.id,
        SiteInput(name="Renamed", address="9 New Road", timezone="Asia/Tokyo"),
    )

    assert (updated_site.name, updated_site.address, updated_site.timezone) == (
        "Renamed",
        "9 New Road",
        "Asia/Tokyo",
    )


def test_update_site_missing_id_raises_entity_not_found_error(db_session: Session):
    with pytest.raises(EntityNotFoundError, match="Site not found"):
        update_site(
            db_session,
            MISSING_SITE_ID,
            SiteInput(name="HQ", address="1 Main Street", timezone="UTC"),
        )


def test_archive_site_sets_archived_and_keeps_row(
    db_session: Session,
    make_site: Callable[..., Site],
):
    site = make_site()
    assert site.id is not None

    archive_site(db_session, site.id)
    stored_site = db_session.get(Site, site.id)

    assert stored_site is not None
    assert stored_site.archived is True


def test_archive_site_missing_id_raises_entity_not_found_error(db_session: Session):
    with pytest.raises(EntityNotFoundError, match="Site not found"):
        archive_site(db_session, MISSING_SITE_ID)


def test_list_sites_query_treats_percent_as_literal(
    db_session: Session,
    make_site: Callable[..., Site],
):
    make_site(name="Depot 100%")
    make_site(name="Depot 1000")

    sites, _ = list_sites(db_session, 20, 0, "100%")

    assert [site.name for site in sites] == ["Depot 100%"]
