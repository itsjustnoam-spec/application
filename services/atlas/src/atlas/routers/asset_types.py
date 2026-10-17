"""
HTTP routes for asset types.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from atlas.database import get_session
from atlas.managers.asset_types import (
    create_asset_type,
    list_live_asset_types,
    soft_delete_asset_type,
    update_asset_type,
)
from atlas.schemas.asset_types import AssetTypeCreate, AssetTypeRead, AssetTypeUpdate

# ----- Consts ----- #

router = APIRouter(prefix="/asset-types")
SessionDependency = Annotated[Session, Depends(get_session)]

# ----- Routes ----- #


@router.get("")
def list_asset_types(session: SessionDependency) -> list[AssetTypeRead]:
    return [
        AssetTypeRead.model_validate(asset_type)
        for asset_type in list_live_asset_types(session)
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_asset_type_route(
    asset_type_create: AssetTypeCreate,
    session: SessionDependency,
) -> AssetTypeRead:
    asset_type = create_asset_type(session, asset_type_create)
    return AssetTypeRead.model_validate(asset_type)


@router.put("/{asset_type_id}")
def update_asset_type_route(
    asset_type_id: int,
    asset_type_update: AssetTypeUpdate,
    session: SessionDependency,
) -> AssetTypeRead:
    asset_type = update_asset_type(
        session,
        asset_type_id,
        asset_type_update,
    )
    return AssetTypeRead.model_validate(asset_type)


@router.delete(
    "/{asset_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_asset_type_route(asset_type_id: int, session: SessionDependency):
    soft_delete_asset_type(session, asset_type_id)
