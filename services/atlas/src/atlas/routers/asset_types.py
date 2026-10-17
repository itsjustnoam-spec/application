"""
Routes for asset types, mounted at the root path because juniper strips the /api/atlas prefix.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from atlas.database import get_session
from atlas.managers import asset_types as asset_type_manager
from atlas.schemas.asset_type import AssetTypeInput, AssetTypeOut
from atlas.schemas.page import Page

# ----- Consts ----- #

router = APIRouter()

# ----- Routes ----- #


@router.get("/asset-types")
def list_asset_types(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    query: Annotated[
        str | None,
        Query(alias="q", max_length=100),
    ] = None,
) -> Page[AssetTypeOut]:
    """
    Lists active asset types matching the search text, one page at a time.
    """
    asset_types, total = asset_type_manager.list_asset_types(
        session,
        limit,
        offset,
        query,
    )
    return Page[AssetTypeOut](
        items=[
            AssetTypeOut.model_validate(asset_type)
            for asset_type in asset_types
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/asset-types", status_code=status.HTTP_201_CREATED)
def create_asset_type(
    asset_type_input: AssetTypeInput,
    session: Annotated[Session, Depends(get_session)],
) -> AssetTypeOut:
    """
    Creates an asset type.
    """
    asset_type = asset_type_manager.create_asset_type(
        session,
        asset_type_input,
    )
    return AssetTypeOut.model_validate(asset_type)


@router.get("/asset-types/{asset_type_id}")
def read_asset_type(
    asset_type_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> AssetTypeOut:
    """
    Reads one active asset type.
    """
    asset_type = asset_type_manager.read_asset_type(
        session,
        asset_type_id,
    )
    return AssetTypeOut.model_validate(asset_type)


@router.put("/asset-types/{asset_type_id}")
def update_asset_type(
    asset_type_id: int,
    asset_type_input: AssetTypeInput,
    session: Annotated[Session, Depends(get_session)],
) -> AssetTypeOut:
    """
    Replaces the name, category, and interval of an active asset type.
    """
    asset_type = asset_type_manager.update_asset_type(
        session,
        asset_type_id,
        asset_type_input,
    )
    return AssetTypeOut.model_validate(asset_type)


@router.delete(
    "/asset-types/{asset_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def archive_asset_type(
    asset_type_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    """
    Archives an active asset type.
    """
    asset_type_manager.archive_asset_type(session, asset_type_id)
