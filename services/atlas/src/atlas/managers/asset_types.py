"""
Data access for asset types, enforcing the live-row and unique-name rules.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from atlas.entities.asset_type import AssetType
from atlas.errors import DuplicateNameError, EntityNotFoundError
from atlas.schemas.asset_types import AssetTypeInput

# ----- Functions ----- #


def list_live_asset_types(session: Session) -> list[AssetType]:
    statement = (
        select(AssetType)
        .where(col(AssetType.is_deleted).is_(False))
        .order_by(col(AssetType.name))
    )
    return list(session.exec(statement).all())


def read_live_asset_type_by_id(session: Session, asset_type_id: int) -> AssetType:
    asset_type: AssetType | None = session.get(AssetType, asset_type_id)
    if asset_type is None or asset_type.is_deleted:
        raise EntityNotFoundError("Asset type not found.")
    return asset_type


def create_asset_type(session: Session, asset_type_input: AssetTypeInput) -> AssetType:
    asset_type = AssetType(
        name=asset_type_input.name,
        category=asset_type_input.category,
        inspection_interval_days=asset_type_input.inspection_interval_days,
    )
    session.add(asset_type)
    commit_asset_type_or_raise_duplicate(session)
    session.refresh(asset_type)
    return asset_type


def update_asset_type(
    session: Session,
    asset_type_id: int,
    asset_type_input: AssetTypeInput,
) -> AssetType:
    asset_type = read_live_asset_type_by_id(session, asset_type_id)
    asset_type.name = asset_type_input.name
    asset_type.category = asset_type_input.category
    asset_type.inspection_interval_days = asset_type_input.inspection_interval_days
    session.add(asset_type)
    commit_asset_type_or_raise_duplicate(session)
    session.refresh(asset_type)
    return asset_type


def soft_delete_asset_type(session: Session, asset_type_id: int):
    asset_type = read_live_asset_type_by_id(session, asset_type_id)
    asset_type.is_deleted = True
    session.add(asset_type)
    session.commit()


def commit_asset_type_or_raise_duplicate(session: Session):
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise DuplicateNameError("An asset type with this name already exists.") from error
