"""
Data access for sites, enforcing the live-row and unique-name rules.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from atlas.entities.site import Site
from atlas.errors import DuplicateNameError, EntityNotFoundError
from atlas.schemas.sites import SiteInput

# ----- Functions ----- #


def list_live_sites(session: Session) -> list[Site]:
    statement = (
        select(Site)
        .where(col(Site.is_deleted).is_(False))
        .order_by(col(Site.name))
    )
    return list(session.exec(statement).all())


def read_live_site_by_id(session: Session, site_id: int) -> Site:
    site: Site | None = session.get(Site, site_id)
    if site is None or site.is_deleted:
        raise EntityNotFoundError("Site not found.")
    return site


def create_site(session: Session, site_input: SiteInput) -> Site:
    site = Site(
        name=site_input.name,
        address=site_input.address,
        timezone=site_input.timezone,
    )
    session.add(site)
    commit_site_or_raise_duplicate(session)
    session.refresh(site)
    return site


def update_site(session: Session, site_id: int, site_input: SiteInput) -> Site:
    site = read_live_site_by_id(session, site_id)
    site.name = site_input.name
    site.address = site_input.address
    site.timezone = site_input.timezone
    session.add(site)
    commit_site_or_raise_duplicate(session)
    session.refresh(site)
    return site


def soft_delete_site(session: Session, site_id: int):
    site = read_live_site_by_id(session, site_id)
    site.is_deleted = True
    session.add(site)
    session.commit()


def commit_site_or_raise_duplicate(session: Session):
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise DuplicateNameError("A site with this name already exists.") from error
