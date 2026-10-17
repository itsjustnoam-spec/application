"""
Data access for asset types: listing, reading, creating, updating, and archiving.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, func, select

from atlas.entities import AssetType
from atlas.managers.errors import DuplicateNameError, EntityNotFoundError
from atlas.schemas.asset_type import AssetTypeInput

# ----- Consts ----- #

ASSET_TYPE_NOT_FOUND_MESSAGE = "Asset type not found"
ASSET_TYPE_NAME_TAKEN = "An asset type with this name already exists"

# ----- Functions ----- #


def list_asset_types(
    session: Session,
    limit: int,
    offset: int,
    query: str | None,
) -> tuple[list[AssetType], int]:
    statement = select(AssetType).where(
        col(AssetType.archived).is_(False),
    )
    if query is not None:
        statement = statement.where(
            col(AssetType.name).icontains(query, autoescape=True),
        )

    total = session.exec(
        select(func.count()).select_from(statement.subquery()),
    ).one()
    asset_types = session.exec(
        statement.order_by(AssetType.name).offset(offset).limit(
            limit,
        ),
    ).all()
    return list(asset_types), total


def read_asset_type(session: Session, asset_type_id: int) -> AssetType:
    asset_type: AssetType | None = session.get(
        AssetType,
        asset_type_id,
    )
    if asset_type is None or asset_type.archived:
        raise EntityNotFoundError(ASSET_TYPE_NOT_FOUND_MESSAGE)

    return asset_type


def create_asset_type(session: Session, data: AssetTypeInput) -> AssetType:
    asset_type = AssetType(
        name=data.name,
        category=data.category,
        inspection_interval_days=data.inspection_interval_days,
    )
    session.add(asset_type)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise DuplicateNameError(ASSET_TYPE_NAME_TAKEN) from error

    session.refresh(asset_type)
    return asset_type


def update_asset_type(
    session: Session,
    asset_type_id: int,
    data: AssetTypeInput,
) -> AssetType:
    asset_type = read_asset_type(session, asset_type_id)
    asset_type.name = data.name
    asset_type.category = data.category
    asset_type.inspection_interval_days = data.inspection_interval_days
    session.add(asset_type)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise DuplicateNameError(ASSET_TYPE_NAME_TAKEN) from error

    session.refresh(asset_type)
    return asset_type


def archive_asset_type(session: Session, asset_type_id: int):
    asset_type = read_asset_type(session, asset_type_id)
    asset_type.archived = True
    session.add(asset_type)
    session.commit()
