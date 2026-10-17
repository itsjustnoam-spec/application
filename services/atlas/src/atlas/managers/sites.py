"""
Data access for sites: listing, reading, creating, updating, and archiving.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import SessionTransaction
from sqlmodel import Session, col, func, select

from atlas.entities import Site
from atlas.managers.errors import DuplicateNameError, EntityNotFoundError
from atlas.schemas.site import SiteInput

# ----- Consts ----- #

SITE_NOT_FOUND_MESSAGE = "Site not found"
SITE_NAME_TAKEN = "A site with this name already exists"

# ----- Functions ----- #


def list_sites(
    session: Session,
    limit: int,
    offset: int,
    query: str | None,
) -> tuple[list[Site], int]:
    """
    Lists active sites, optionally filtered by name, one page at a time.

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
    page_statement = statement.order_by(col(Site.name), col(Site.id))
    sites = session.exec(
        page_statement.offset(offset).limit(limit),
    ).all()
    return list(sites), total


def read_site(session: Session, site_id: int) -> Site:
    """
    Reads one active site.

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
    savepoint: SessionTransaction,
):
    """
    Writes the site changes made inside a savepoint, and closes it.

    :param session: The request's database session.
    :param savepoint: The savepoint opened before the changes were made.
    :raises DuplicateNameError: When another active site has the same name.
    """
    try:
        session.flush()
    except IntegrityError as error:
        savepoint.rollback()
        raise DuplicateNameError(SITE_NAME_TAKEN) from error

    savepoint.commit()


def create_site(session: Session, site_input: SiteInput) -> Site:
    """
    Creates a site.

    :param session: The request's database session.
    :param site_input: The values of the new site.
    :return: The created site.
    :raises DuplicateNameError: When an active site already has this name.
    """
    savepoint = session.begin_nested()
    site = Site(
        name=site_input.name,
        address=site_input.address,
        timezone=site_input.timezone,
    )
    session.add(site)
    flush_site_changes(session, savepoint)
    return site


def update_site(
    session: Session,
    site_id: int,
    site_input: SiteInput,
) -> Site:
    """
    Replaces the name, address, and timezone of an active site.

    :param session: The request's database session.
    :param site_id: The id of the site.
    :param site_input: The new values of the site.
    :return: The updated site.
    :raises EntityNotFoundError: When the site doesn't exist or is archived.
    :raises DuplicateNameError: When another active site has the new name.
    """
    site = read_site(session, site_id)
    savepoint = session.begin_nested()
    site.name = site_input.name
    site.address = site_input.address
    site.timezone = site_input.timezone
    flush_site_changes(session, savepoint)
    return site


def archive_site(session: Session, site_id: int):
    """
    Archives an active site, which hides it and frees its name.

    :param session: The request's database session.
    :param site_id: The id of the site.
    :raises EntityNotFoundError: When the site doesn't exist or is archived.
    """
    site = read_site(session, site_id)
    site.archived = True
    session.flush()
