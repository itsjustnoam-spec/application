from collections.abc import Callable

import pytest
from sqlmodel import Session

from atlas.entities import AssetCategory, AssetType


@pytest.fixture
def make_asset_type(db_session: Session) -> Callable[..., AssetType]:
    def _make(
        name: str = "Pump",
        category: AssetCategory = AssetCategory.MECHANICAL,
        inspection_interval_days: int = 30,
        archived: bool = False,
    ) -> AssetType:
        asset_type = AssetType(
            name=name,
            category=category,
            inspection_interval_days=inspection_interval_days,
            archived=archived,
        )
        db_session.add(asset_type)
        db_session.commit()
        db_session.refresh(asset_type)
        return asset_type

    return _make
