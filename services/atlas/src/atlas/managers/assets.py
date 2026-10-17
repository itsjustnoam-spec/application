"""
Data access for assets: listing, reading, creating, updating, and archiving.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from datetime import date
from typing import Any

from sqlalchemy import ColumnElement, Date, case, cast, func, null, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import SessionTransaction
from sqlalchemy.sql.elements import UnaryExpression
from sqlmodel import Session, col, select

from atlas.entities import Asset, AssetStatus, AssetType, Site
from atlas.managers.asset_types import lock_asset_type, read_asset_type
from atlas.managers.due_dates import (
    STATUSES_WITHOUT_DUE_DATE,
    is_overdue,
    next_inspection_due,
)
from atlas.managers.errors import (
    DuplicateSerialNumberError,
    EntityNotFoundError,
)
from atlas.managers.sites import lock_site, read_site
from atlas.schemas.asset import AssetInput, AssetOut, AssetSort, SortDirection

# ----- Consts ----- #

ASSET_NOT_FOUND_MESSAGE = "Asset not found"
ASSET_SERIAL_NUMBER_TAKEN = "An asset with this serial number already exists"

# ----- Functions ----- #


def to_asset_out(
    asset: Asset,
    site: Site,
    asset_type: AssetType,
) -> AssetOut:
    """
    Build the API view of an asset, with its due date and overdue flag.

    :param asset: The asset row.
    :param site: The asset's site.
    :param asset_type: The asset's asset type, which holds the inspection interval.
    :return: The asset as the API returns it.
    """
    due_date = next_inspection_due(
        asset.installation_date,
        asset_type.inspection_interval_days,
        asset.status,
    )
    return AssetOut(
        id=asset.id,
        name=asset.name,
        serial_number=asset.serial_number,
        site_id=site.id,
        site_name=site.name,
        site_timezone=site.timezone,
        asset_type_id=asset_type.id,
        asset_type_name=asset_type.name,
        status=asset.status,
        installation_date=asset.installation_date,
        notes=asset.notes,
        next_inspection_due=due_date,
        is_overdue=is_overdue(due_date, site.timezone),
        archived=asset.archived,
    )


def next_due_expression() -> ColumnElement[date]:
    """
    Build the SQL expression for the next inspection due date, null for statuses without one.

    :return: A SQL expression usable in ORDER BY.
    """
    interval = func.make_interval(
        0,
        0,
        0,
        AssetType.inspection_interval_days,
    )
    return case(
        (
            col(Asset.status).not_in(STATUSES_WITHOUT_DUE_DATE),
            cast(Asset.installation_date + interval, Date),
        ),
        else_=null(),
    )


def list_assets(
    session: Session,
    limit: int,
    offset: int,
    query: str | None,
    site_id: int | None,
    asset_type_id: int | None,
    status: AssetStatus | None,
    sort: AssetSort,
    direction: SortDirection,
) -> tuple[list[AssetOut], int]:
    """
    List active assets, filtered and sorted, one page at a time.

    :param session: The request's database session.
    :param limit: The maximum number of assets to return.
    :param offset: How many assets to skip before the page starts.
    :param query: Text the name or serial number must contain, or None for all.
    :param site_id: Only assets at this site, or None for all sites.
    :param asset_type_id: Only assets of this asset type, or None for all types.
    :param status: Only assets with this status, or None for all statuses.
    :param sort: The column to sort by.
    :param direction: The order of the sort.
    :return: The assets of the page, and the total number that match.
    """
    archived_filter = col(Asset.archived).is_(False)
    conditions: list[ColumnElement[bool]] = [archived_filter]
    if query is not None:
        conditions.append(
            or_(
                col(Asset.name).icontains(
                    query,
                    autoescape=True,
                ),
                col(Asset.serial_number).icontains(
                    query,
                    autoescape=True,
                ),
            ),
        )

    if site_id is not None:
        conditions.append(col(Asset.site_id) == site_id)

    if asset_type_id is not None:
        conditions.append(col(Asset.asset_type_id) == asset_type_id)

    if status is not None:
        conditions.append(col(Asset.status) == status)

    total = session.exec(
        select(func.count()).select_from(Asset).where(*conditions),
    ).one()

    primary_order: UnaryExpression[Any]
    if sort == AssetSort.NAME:
        name_key = col(Asset.name)
        primary_order = (
            name_key.asc()
            if direction == SortDirection.ASC
            else name_key.desc()
        )
    else:
        due_key = next_due_expression()
        primary_order = (
            due_key.asc().nulls_last()
            if direction == SortDirection.ASC
            else due_key.desc().nulls_last()
        )

    site_join = col(Asset.site_id) == col(Site.id)
    asset_type_join = col(Asset.asset_type_id) == col(AssetType.id)
    statement = (
        select(
            Asset,
            Site,
            AssetType,
        )
        .join(
            Site,
            site_join,
        )
        .join(
            AssetType,
            asset_type_join,
        )
        .where(
            *conditions,
        )
        .order_by(
            primary_order,
            col(Asset.id).asc(),
        )
    )
    rows = session.exec(statement.offset(offset).limit(limit)).all()
    assets = [
        to_asset_out(
            asset,
            site,
            asset_type,
        )
        for asset, site, asset_type in rows
    ]
    return assets, total


def _read_active_asset(session: Session, asset_id: int) -> Asset:
    """
    Read one active asset row.

    :param session: The request's database session.
    :param asset_id: The id of the asset.
    :return: The asset row.
    :raises EntityNotFoundError: When the asset doesn't exist or is archived.
    """
    asset: Asset | None = session.get(Asset, asset_id)
    if asset is None or asset.archived:
        raise EntityNotFoundError(ASSET_NOT_FOUND_MESSAGE)

    return asset


def _asset_out_for(session: Session, asset: Asset) -> AssetOut:
    """
    Build the API view of an asset, loading its site and asset type.

    :param session: The request's database session.
    :param asset: The asset row.
    :return: The asset as the API returns it.
    """
    site = read_site(session, asset.site_id)
    asset_type = read_asset_type(session, asset.asset_type_id)
    return to_asset_out(
        asset,
        site,
        asset_type,
    )


def read_asset(session: Session, asset_id: int) -> AssetOut:
    """
    Read one active asset.

    :param session: The request's database session.
    :param asset_id: The id of the asset.
    :return: The asset as the API returns it.
    :raises EntityNotFoundError: When the asset doesn't exist or is archived.
    """
    asset = _read_active_asset(session, asset_id)
    return _asset_out_for(session, asset)


def _check_references(session: Session, asset_input: AssetInput):
    """
    Check that the site and asset type of an asset are active.

    :param session: The request's database session.
    :param asset_input: The values of the asset.
    :raises EntityNotFoundError: When the site or asset type is missing or archived.
    """
    lock_site(
        session,
        asset_input.site_id,
        exclusive=False,
    )
    lock_asset_type(
        session,
        asset_input.asset_type_id,
        exclusive=False,
    )
    read_site(session, asset_input.site_id)
    read_asset_type(session, asset_input.asset_type_id)


def flush_asset_changes(
    session: Session,
    transaction: SessionTransaction,
):
    """
    Write the asset changes made inside a nested transaction, and close it.

    :param session: The request's database session.
    :param transaction: The nested transaction opened before the changes were made.
    :raises DuplicateSerialNumberError: When another active asset has the same serial number.
    """
    try:
        session.flush()
    except IntegrityError as error:
        transaction.rollback()
        raise DuplicateSerialNumberError(
            ASSET_SERIAL_NUMBER_TAKEN,
        ) from error

    transaction.commit()


def _apply_input(asset: Asset, asset_input: AssetInput):
    """
    Copy the editable values of an asset input onto an asset row.

    :param asset: The asset row to change.
    :param asset_input: The new values.
    """
    asset.name = asset_input.name
    asset.serial_number = asset_input.serial_number
    asset.site_id = asset_input.site_id
    asset.asset_type_id = asset_input.asset_type_id
    asset.status = asset_input.status
    asset.installation_date = asset_input.installation_date
    asset.notes = asset_input.notes


def create_asset(session: Session, asset_input: AssetInput) -> AssetOut:
    """
    Create an asset at an active site, of an active asset type.

    :param session: The request's database session.
    :param asset_input: The values of the new asset.
    :return: The created asset as the API returns it.
    :raises EntityNotFoundError: When the site or asset type is missing or archived.
    :raises DuplicateSerialNumberError: When an active asset has this serial number.
    """
    _check_references(session, asset_input)
    transaction = session.begin_nested()
    asset = Asset(
        name=asset_input.name,
        serial_number=asset_input.serial_number,
        site_id=asset_input.site_id,
        asset_type_id=asset_input.asset_type_id,
        status=asset_input.status,
        installation_date=asset_input.installation_date,
        notes=asset_input.notes,
    )
    session.add(asset)
    flush_asset_changes(session, transaction)
    return _asset_out_for(session, asset)


def update_asset(
    session: Session,
    asset_id: int,
    asset_input: AssetInput,
) -> AssetOut:
    """
    Replace the editable values of an active asset.

    :param session: The request's database session.
    :param asset_id: The id of the asset.
    :param asset_input: The new values of the asset.
    :return: The updated asset as the API returns it.
    :raises EntityNotFoundError: When the asset, its site, or its asset type is missing or archived.
    :raises DuplicateSerialNumberError: When another active asset has the serial number.
    """
    asset = _read_active_asset(session, asset_id)
    _check_references(session, asset_input)
    transaction = session.begin_nested()
    _apply_input(asset, asset_input)
    flush_asset_changes(session, transaction)
    return _asset_out_for(session, asset)


def archive_asset(session: Session, asset_id: int):
    """
    Archive an active asset, which hides it and frees its serial number.

    :param session: The request's database session.
    :param asset_id: The id of the asset.
    :raises EntityNotFoundError: When the asset doesn't exist or is archived.
    """
    asset = _read_active_asset(session, asset_id)
    asset.archived = True
    session.flush()
