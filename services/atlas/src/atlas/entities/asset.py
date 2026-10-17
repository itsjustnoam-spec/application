"""
Asset table model with the status enum, the site and asset type references, and the installation date.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from datetime import date
from enum import StrEnum

from sqlalchemy import Index, text
from sqlmodel import Field, SQLModel

# ----- Consts ----- #

MAX_NOTES_LENGTH = 1000

# ----- Classes ----- #


class AssetStatus(StrEnum):
    """
    The operating state of an asset.
    """
    OPERATIONAL = "Operational"
    NEEDS_ATTENTION = "Needs attention"
    OUT_OF_SERVICE = "Out of service"
    RETIRED = "Retired"


class Asset(SQLModel, table=True):
    """
    One piece of equipment at a site, of one asset type.
    """
    __tablename__ = "asset"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    serial_number: str = Field(max_length=100)
    site_id: int = Field(
        foreign_key="site.id",
        index=True,
    )
    asset_type_id: int = Field(
        foreign_key="asset_type.id",
        index=True,
    )
    status: AssetStatus
    installation_date: date
    notes: str | None = Field(
        default=None,
        max_length=MAX_NOTES_LENGTH,
    )
    archived: bool = Field(default=False)

    __table_args__ = (
        Index(
            "uq_asset_serial_number_active",
            "serial_number",
            unique=True,
            postgresql_where=text("archived = false"),
        ),
    )
