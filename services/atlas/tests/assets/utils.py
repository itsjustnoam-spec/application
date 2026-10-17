from datetime import UTC, datetime, tzinfo
from typing import Any

from sqlmodel import Session

from atlas.entities import AssetStatus
from atlas.managers.assets import list_assets
from atlas.schemas.asset import AssetOut, AssetSort, SortDirection

FROZEN_MOMENT = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)


class FrozenDatetime(datetime):
    @classmethod
    def now(cls, tz: tzinfo | None = None) -> datetime:
        return FROZEN_MOMENT.astimezone(tz)


def build_asset_body(
    site_id: int,
    asset_type_id: int,
    **overrides: Any,
) -> dict[str, Any]:
    return {
        "name": "Compressor",
        "serial_number": "SN-1",
        "site_id": site_id,
        "asset_type_id": asset_type_id,
        "status": "Operational",
        "installation_date": "2026-01-01",
        "notes": None,
        **overrides,
    }


def names_of(assets: list[AssetOut]) -> list[str]:
    return [
        asset.name
        for asset in assets
    ]


def values_of(items: list[dict[str, Any]], key: str) -> list[Any]:
    return [
        item[key]
        for item in items
    ]


def list_page(
    db_session: Session,
    query: str | None = None,
    site_id: int | None = None,
    asset_type_id: int | None = None,
    status: AssetStatus | None = None,
    sort: AssetSort = AssetSort.NAME,
    direction: SortDirection = SortDirection.ASC,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[AssetOut], int]:
    return list_assets(
        db_session,
        limit,
        offset,
        query,
        site_id,
        asset_type_id,
        status,
        sort,
        direction,
    )


def count_assets(db_session: Session) -> int:
    _, total = list_page(db_session)
    return total
