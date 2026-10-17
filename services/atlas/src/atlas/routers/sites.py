"""
HTTP routes for sites.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from atlas.database import get_session
from atlas.managers.sites import (
    create_site,
    list_live_sites,
    soft_delete_site,
    update_site,
)
from atlas.schemas.sites import SiteCreate, SiteRead, SiteUpdate

# ----- Consts ----- #

router = APIRouter(prefix="/sites")
SessionDependency = Annotated[Session, Depends(get_session)]

# ----- Routes ----- #


@router.get("")
def list_sites(session: SessionDependency) -> list[SiteRead]:
    return [SiteRead.model_validate(site) for site in list_live_sites(session)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_site_route(
    site_create: SiteCreate,
    session: SessionDependency,
) -> SiteRead:
    site = create_site(session, site_create)
    return SiteRead.model_validate(site)


@router.put("/{site_id}")
def update_site_route(
    site_id: int,
    site_update: SiteUpdate,
    session: SessionDependency,
) -> SiteRead:
    site = update_site(
        session,
        site_id,
        site_update,
    )
    return SiteRead.model_validate(site)


@router.delete(
    "/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_site_route(site_id: int, session: SessionDependency):
    soft_delete_site(session, site_id)
