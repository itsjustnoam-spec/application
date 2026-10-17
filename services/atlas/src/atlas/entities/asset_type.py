"""
Asset type table model for the Atlas service.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from sqlalchemy import CheckConstraint
from sqlmodel import Field, SQLModel

# ----- Classes ----- #


class AssetType(SQLModel, table=True):
    """
    A kind of asset, with the number of days between its inspections.
    """

    __tablename__ = "asset_types"
    __table_args__ = (
        CheckConstraint(
            "inspection_interval_days BETWEEN 1 AND 3650",
            name="ck_asset_types_inspection_interval_days_range",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    category: str = Field(max_length=100)
    inspection_interval_days: int
    is_deleted: bool = Field(default=False)
