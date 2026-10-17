"""
Request and response schemas for the asset types endpoints.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from pydantic import BaseModel, ConfigDict, Field

# ----- Classes ----- #


class AssetTypeInput(BaseModel):
    """
    Writable fields of an asset type, shared by create and update requests.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=100)
    inspection_interval_days: int = Field(ge=1, le=3650)


class AssetTypeCreate(AssetTypeInput):
    """
    Request body for creating an asset type.
    """


class AssetTypeUpdate(AssetTypeInput):
    """
    Request body for replacing an asset type.
    """


class AssetTypeRead(BaseModel):
    """
    Response body describing an asset type.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    inspection_interval_days: int
