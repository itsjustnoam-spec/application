"""
Data access for sites: listing, reading, creating, updating, and archiving.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import SessionTransaction
from sqlmodel import Session, col, func, select

from atlas.entities import Asset, Site
from atlas.managers.errors import (
    DuplicateNameError,
    EntityInUseError,
    EntityNotFoundError,
)
from atlas.schemas.site import SiteInput

# ----- Consts ----- #

SITE_NOT_FOUND_MESSAGE = "Site not found"
SITE_NAME_TAKEN = "A site with this name already exists"
SITE_HAS_ACTIVE_ASSETS = "Site has active assets"

# ----- Functions ----- #


def list_sites(
    session: Session,
    limit: int,
    offset: int,
    query: str | None,
) -> tuple[list[Site], int]:
    """
    List active sites, optionally filtered by name, one page at a time.

    :param session: The request's database session.
    :param limit: The maximum number of sites to return.
    :param offset: How many sites to skip before the page starts.
    :param query: Text the site name must contain, or None for all sites.
    :return: The sites of the page, and the total number of matching sites.
    """
    statement = select(Site).where(col(Site.archived).is_(False))
    if query is not None:
        statement = statement.where(
            col(Site.name).icontains(query, autoescape=True),
        )

    total = session.exec(
        select(func.count()).select_from(statement.subquery()),
    ).one()
    page_statement = statement.order_by(Site.name)
    sites = session.exec(
        page_statement.offset(offset).limit(limit),
    ).all()
    return list(sites), total


def lock_site(session: Session, site_id: int, exclusive: bool):
    """
    Lock a site row so an archive and an asset reference to it cannot race.

    :param session: The request's database session.
    :param site_id: The id of the site.
    :param exclusive: True to block other writers and references (archive), False to only block archives.
    """
    statement = (
        select(Site)
        .where(col(Site.id) == site_id)
        .with_for_update(
            read=not exclusive,
        )
    )
    session.exec(
        statement.execution_options(
            populate_existing=True,
        ),
    ).first()


def read_site(session: Session, site_id: int) -> Site:
    """
    Read one active site.

    :param session: The request's database session.
    :param site_id: The id of the site.
    :return: The site.
    :raises EntityNotFoundError: When the site doesn't exist or is archived.
    """
    site: Site | None = session.get(Site, site_id)
    if site is None or site.archived:
        raise EntityNotFoundError(SITE_NOT_FOUND_MESSAGE)

    return site


def flush_site_changes(
    session: Session,
    transaction: SessionTransaction,
):
    """
    Write the site changes made inside a nested transaction, and close it.

    :param session: The request's database session.
    :param transaction: The nested transaction opened before the changes were made.
    :raises DuplicateNameError: When another active site has the same name.
    """
    try:
        session.flush()
    except IntegrityError as error:
        transaction.rollback()
        raise DuplicateNameError(SITE_NAME_TAKEN) from error

    transaction.commit()


def create_site(session: Session, site_input: SiteInput) -> Site:
    """
    Create a site.

    :param session: The request's database session.
    :param site_input: The values of the new site.
    :return: The created site.
    :raises DuplicateNameError: When an active site already has this name.
    """
    transaction = session.begin_nested()
    site = Site(
        name=site_input.name,
        address=site_input.address,
        timezone=site_input.timezone,
    )
    session.add(site)
    flush_site_changes(session, transaction)
    return site


def update_site(
    session: Session,
    site_id: int,
    site_input: SiteInput,
) -> Site:
    """
    Replace the name, address, and timezone of an active site.

    :param session: The request's database session.
    :param site_id: The id of the site.
    :param site_input: The new values of the site.
    :return: The updated site.
    :raises EntityNotFoundError: When the site doesn't exist or is archived.
    :raises DuplicateNameError: When another active site has the new name.
    """
    site = read_site(session, site_id)
    transaction = session.begin_nested()
    site.name = site_input.name
    site.address = site_input.address
    site.timezone = site_input.timezone
    flush_site_changes(session, transaction)
    return site


def archive_site(session: Session, site_id: int):
    """
    Archive an active site, which hides it and frees its name.

    :param session: The request's database session.
    :param site_id: The id of the site.
    :raises EntityNotFoundError: When the site doesn't exist or is archived.
    :raises EntityInUseError: When an active asset is still at the site.
    """
    lock_site(
        session,
        site_id,
        exclusive=True,
    )
    site = read_site(session, site_id)
    active_assets = select(Asset.id).where(
        col(Asset.site_id) == site_id,
        col(Asset.archived).is_(False),
    )
    first_active_asset = session.exec(active_assets.limit(1)).first()
    has_active_assets = first_active_asset is not None
    if has_active_assets:
        raise EntityInUseError(SITE_HAS_ACTIVE_ASSETS)

    site.archived = True
    session.flush()
