"""
Data access for asset types: listing, reading, creating, updating, and archiving.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import SessionTransaction
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
    """
    Lists active asset types, optionally filtered by name, one page at a time.

    :param session: The request's database session.
    :param limit: The maximum number of asset types to return.
    :param offset: How many asset types to skip before the page starts.
    :param query: Text the name must contain, or None for all asset types.
    :return: The asset types of the page, and the total number that match.
    """
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
    page_statement = statement.order_by(
        col(AssetType.name),
        col(AssetType.id),
    )
    asset_types = session.exec(
        page_statement.offset(offset).limit(limit),
    ).all()
    return list(asset_types), total


def read_asset_type(session: Session, asset_type_id: int) -> AssetType:
    """
    Reads one active asset type.

    :param session: The request's database session.
    :param asset_type_id: The id of the asset type.
    :return: The asset type.
    :raises EntityNotFoundError: When it doesn't exist or is archived.
    """
    asset_type: AssetType | None = session.get(
        AssetType,
        asset_type_id,
    )
    if asset_type is None or asset_type.archived:
        raise EntityNotFoundError(ASSET_TYPE_NOT_FOUND_MESSAGE)

    return asset_type


def flush_asset_type_changes(
    session: Session,
    savepoint: SessionTransaction,
):
    """
    Writes the asset type changes made inside a savepoint, and closes it.

    :param session: The request's database session.
    :param savepoint: The savepoint opened before the changes were made.
    :raises DuplicateNameError: When another active asset type has the same name.
    """
    try:
        session.flush()
    except IntegrityError as error:
        savepoint.rollback()
        raise DuplicateNameError(ASSET_TYPE_NAME_TAKEN) from error

    savepoint.commit()


def create_asset_type(
    session: Session,
    asset_type_input: AssetTypeInput,
) -> AssetType:
    """
    Creates an asset type.

    :param session: The request's database session.
    :param asset_type_input: The values of the new asset type.
    :return: The created asset type.
    :raises DuplicateNameError: When an active asset type has this name.
    """
    savepoint = session.begin_nested()
    asset_type = AssetType(
        name=asset_type_input.name,
        category=asset_type_input.category,
        inspection_interval_days=asset_type_input.inspection_interval_days,
    )
    session.add(asset_type)
    flush_asset_type_changes(session, savepoint)
    return asset_type


def update_asset_type(
    session: Session,
    asset_type_id: int,
    asset_type_input: AssetTypeInput,
) -> AssetType:
    """
    Replaces the name, category, and interval of an active asset type.

    :param session: The request's database session.
    :param asset_type_id: The id of the asset type.
    :param asset_type_input: The new values of the asset type.
    :return: The updated asset type.
    :raises EntityNotFoundError: When it doesn't exist or is archived.
    :raises DuplicateNameError: When another active asset type has the name.
    """
    asset_type = read_asset_type(session, asset_type_id)
    savepoint = session.begin_nested()
    asset_type.name = asset_type_input.name
    asset_type.category = asset_type_input.category
    asset_type.inspection_interval_days = (
        asset_type_input.inspection_interval_days
    )
    flush_asset_type_changes(session, savepoint)
    return asset_type


def archive_asset_type(session: Session, asset_type_id: int):
    """
    Archives an active asset type, which hides it and frees its name.

    :param session: The request's database session.
    :param asset_type_id: The id of the asset type.
    :raises EntityNotFoundError: When it doesn't exist or is archived.
    """
    asset_type = read_asset_type(session, asset_type_id)
    asset_type.archived = True
    session.flush()
