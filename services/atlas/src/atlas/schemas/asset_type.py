"""
Request and response schemas for asset types.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from pydantic import BaseModel, ConfigDict, Field

from atlas.entities.asset_type import (
    MAX_INSPECTION_INTERVAL_DAYS,
    MIN_INSPECTION_INTERVAL_DAYS,
    AssetCategory,
)

# ----- Classes ----- #


class AssetTypeInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    category: AssetCategory
    inspection_interval_days: int = Field(
        ge=MIN_INSPECTION_INTERVAL_DAYS,
        le=MAX_INSPECTION_INTERVAL_DAYS,
    )


class AssetTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: AssetCategory
    inspection_interval_days: int
    archived: bool
