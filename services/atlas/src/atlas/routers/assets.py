"""
Routes for assets, mounted at the root path because juniper strips the /api/atlas prefix.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from atlas.database import get_session
from atlas.entities import AssetStatus
from atlas.managers import assets as asset_manager
from atlas.schemas.asset import (
    AssetInput,
    AssetOut,
    AssetSort,
    SortDirection,
)
from atlas.schemas.page import Page

# ----- Consts ----- #

router = APIRouter()

# ----- Routes ----- #


@router.get("/assets")
def list_assets(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    query: Annotated[
        str | None,
        Query(alias="q", max_length=100),
    ] = None,
    site_id: int | None = None,
    asset_type_id: int | None = None,
    status_filter: Annotated[
        AssetStatus | None,
        Query(alias="status"),
    ] = None,
    sort: AssetSort = AssetSort.NAME,
    direction: SortDirection = SortDirection.ASC,
) -> Page[AssetOut]:
    """
    List active assets matching the search text and filters, one page at a time.
    """
    assets, total = asset_manager.list_assets(
        session,
        limit,
        offset,
        query,
        site_id,
        asset_type_id,
        status_filter,
        sort,
        direction,
    )
    return Page[AssetOut](
        items=assets,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/assets", status_code=status.HTTP_201_CREATED)
def create_asset(
    asset_input: AssetInput,
    session: Annotated[Session, Depends(get_session)],
) -> AssetOut:
    """
    Create an asset at an active site, of an active asset type.
    """
    return asset_manager.create_asset(session, asset_input)


@router.get("/assets/{asset_id}")
def read_asset(
    asset_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> AssetOut:
    """
    Read one active asset.
    """
    return asset_manager.read_asset(session, asset_id)


@router.put("/assets/{asset_id}")
def update_asset(
    asset_id: int,
    asset_input: AssetInput,
    session: Annotated[Session, Depends(get_session)],
) -> AssetOut:
    """
    Replace the editable values of an active asset.
    """
    return asset_manager.update_asset(
        session,
        asset_id,
        asset_input,
    )


@router.delete(
    "/assets/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def archive_asset(
    asset_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    """
    Archive an active asset.
    """
    asset_manager.archive_asset(session, asset_id)
