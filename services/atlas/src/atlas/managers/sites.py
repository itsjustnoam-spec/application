"""
Data access for sites: listing, reading, creating, updating, and archiving.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from sqlalchemy.exc import IntegrityError
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
    statement = select(Site).where(col(Site.archived).is_(False))
    if query is not None:
        statement = statement.where(
            col(Site.name).icontains(query, autoescape=True),
        )

    total = session.exec(
        select(func.count()).select_from(statement.subquery()),
    ).one()
    sites = session.exec(
        statement.order_by(Site.name).offset(offset).limit(limit),
    ).all()
    return list(sites), total


def read_site(session: Session, site_id: int) -> Site:
    site: Site | None = session.get(Site, site_id)
    if site is None or site.archived:
        raise EntityNotFoundError(SITE_NOT_FOUND_MESSAGE)

    return site


def create_site(session: Session, data: SiteInput) -> Site:
    site = Site(
        name=data.name,
        address=data.address,
        timezone=data.timezone,
    )
    session.add(site)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise DuplicateNameError(SITE_NAME_TAKEN) from error

    session.refresh(site)
    return site


def update_site(session: Session, site_id: int, data: SiteInput) -> Site:
    site = read_site(session, site_id)
    site.name = data.name
    site.address = data.address
    site.timezone = data.timezone
    session.add(site)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise DuplicateNameError(SITE_NAME_TAKEN) from error

    session.refresh(site)
    return site


def archive_site(session: Session, site_id: int):
    site = read_site(session, site_id)
    site.archived = True
    session.add(site)
    session.commit()
