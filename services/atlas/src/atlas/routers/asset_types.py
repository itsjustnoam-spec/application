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

SessionDep = Annotated[Session, Depends(get_session)]

# ----- Routes ----- #


@router.get("/asset-types")
def list_asset_types(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> Page[AssetTypeOut]:
    asset_types, total = asset_type_manager.list_asset_types(
        session,
        limit,
        offset,
        q,
    )
    return Page[AssetTypeOut](
        items=[
            AssetTypeOut.model_validate(item)
            for item in asset_types
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/asset-types", status_code=status.HTTP_201_CREATED)
def create_asset_type(
    data: AssetTypeInput,
    session: SessionDep,
) -> AssetTypeOut:
    asset_type = asset_type_manager.create_asset_type(session, data)
    return AssetTypeOut.model_validate(asset_type)


@router.get("/asset-types/{asset_type_id}")
def read_asset_type(
    asset_type_id: int,
    session: SessionDep,
) -> AssetTypeOut:
    asset_type = asset_type_manager.read_asset_type(
        session,
        asset_type_id,
    )
    return AssetTypeOut.model_validate(asset_type)


@router.put("/asset-types/{asset_type_id}")
def update_asset_type(
    asset_type_id: int,
    data: AssetTypeInput,
    session: SessionDep,
) -> AssetTypeOut:
    asset_type = asset_type_manager.update_asset_type(
        session,
        asset_type_id,
        data,
    )
    return AssetTypeOut.model_validate(asset_type)


@router.delete(
    "/asset-types/{asset_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def archive_asset_type(asset_type_id: int, session: SessionDep):
    asset_type_manager.archive_asset_type(session, asset_type_id)
