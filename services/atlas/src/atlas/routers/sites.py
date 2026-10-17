"""
Routes for sites, mounted at the root path because juniper strips the /api/atlas prefix.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from atlas.database import get_session
from atlas.managers import sites as site_manager
from atlas.schemas.page import Page
from atlas.schemas.site import SiteInput, SiteOut

# ----- Consts ----- #

router = APIRouter()

# ----- Routes ----- #


@router.get("/sites")
def list_sites(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    query: Annotated[
        str | None,
        Query(alias="q", max_length=100),
    ] = None,
) -> Page[SiteOut]:
    """
    List active sites matching the search text, one page at a time.
    """
    sites, total = site_manager.list_sites(
        session,
        limit,
        offset,
        query,
    )
    return Page[SiteOut](
        items=[
            SiteOut.model_validate(site)
            for site in sites
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/sites", status_code=status.HTTP_201_CREATED)
def create_site(
    site_input: SiteInput,
    session: Annotated[Session, Depends(get_session)],
) -> SiteOut:
    """
    Create a site.
    """
    site = site_manager.create_site(session, site_input)
    return SiteOut.model_validate(site)


@router.get("/sites/{site_id}")
def read_site(
    site_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> SiteOut:
    """
    Read one active site.
    """
    site = site_manager.read_site(session, site_id)
    return SiteOut.model_validate(site)


@router.put("/sites/{site_id}")
def update_site(
    site_id: int,
    site_input: SiteInput,
    session: Annotated[Session, Depends(get_session)],
) -> SiteOut:
    """
    Replace the name, address, and timezone of an active site.
    """
    site = site_manager.update_site(
        session,
        site_id,
        site_input,
    )
    return SiteOut.model_validate(site)


@router.delete(
    "/sites/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def archive_site(
    site_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    """
    Archive an active site.
    """
    site_manager.archive_site(session, site_id)
