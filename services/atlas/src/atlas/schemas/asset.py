"""
Request and response schemas for assets.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from atlas.entities.asset import MAX_NOTES_LENGTH, AssetStatus

# ----- Classes ----- #


class AssetSort(StrEnum):
    """
    The columns an asset list can be sorted by.
    """
    NAME = "name"
    NEXT_INSPECTION_DUE = "next_inspection_due"


class SortDirection(StrEnum):
    """
    The order of a sorted list.
    """
    ASC = "asc"
    DESC = "desc"


class AssetInput(BaseModel):
    """
    The values a client sends to create or update an asset.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    serial_number: str = Field(min_length=1, max_length=100)
    site_id: int
    asset_type_id: int
    status: AssetStatus
    installation_date: date
    notes: str | None = Field(
        default=None,
        max_length=MAX_NOTES_LENGTH,
    )

    @field_validator("notes")
    @classmethod
    def blank_notes_to_none(cls, notes: str | None) -> str | None:
        """
        Store an empty or whitespace-only note as no note.

        :param notes: The notes the client sent.
        :return: The stripped notes, or None when nothing is left.
        """
        if notes is None or len(notes.strip()) == 0:
            return None

        return notes.strip()


class AssetOut(BaseModel):
    """
    An asset as the API returns it, with its site and asset type details and due date.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    serial_number: str
    site_id: int
    site_name: str
    site_timezone: str
    asset_type_id: int
    asset_type_name: str
    status: AssetStatus
    installation_date: date
    notes: str | None
    next_inspection_due: date | None
    is_overdue: bool
    archived: bool
