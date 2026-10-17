"""
Asset type table model with the category enum and inspection interval.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from enum import StrEnum

from sqlalchemy import CheckConstraint, Index, text
from sqlmodel import Field, SQLModel

# ----- Consts ----- #

MIN_INSPECTION_INTERVAL_DAYS = 1
MAX_INSPECTION_INTERVAL_DAYS = 3650

# ----- Classes ----- #


class AssetCategory(StrEnum):
    """
    The kind of equipment an asset type describes.
    """
    ELECTRICAL = "Electrical"
    MECHANICAL = "Mechanical"
    HVAC = "HVAC"
    SAFETY = "Safety"
    OTHER = "Other"


class AssetType(SQLModel, table=True):
    """
    A kind of asset, with how often its units must be inspected.
    """
    __tablename__ = "asset_type"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    category: AssetCategory
    inspection_interval_days: int
    archived: bool = Field(default=False)

    __table_args__ = (
        Index(
            "uq_asset_type_name_active",
            "name",
            unique=True,
            postgresql_where=text("archived = false"),
        ),
        CheckConstraint(
            f"inspection_interval_days BETWEEN {MIN_INSPECTION_INTERVAL_DAYS} "
            f"AND {MAX_INSPECTION_INTERVAL_DAYS}",
            name="ck_asset_type_inspection_interval_days_range",
        ),
    )
