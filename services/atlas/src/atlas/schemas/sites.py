"""
Request and response schemas for the sites endpoints.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from zoneinfo import available_timezones

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

# ----- Consts ----- #

KNOWN_TIMEZONES: frozenset[str] = frozenset(available_timezones())

# ----- Classes ----- #


class SiteInput(BaseModel):
    """
    Writable fields of a site, shared by create and update requests.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=1, max_length=255)
    timezone: str = Field(max_length=64)

    @field_validator("timezone")
    @classmethod
    def check_timezone_is_known(cls, value: str) -> str:
        if value not in KNOWN_TIMEZONES:
            raise PydanticCustomError(
                "unknown_timezone",
                "Timezone must be an IANA name such as 'Europe/Berlin'.",
            )
        return value


class SiteCreate(SiteInput):
    """
    Request body for creating a site.
    """


class SiteUpdate(SiteInput):
    """
    Request body for replacing a site.
    """


class SiteRead(BaseModel):
    """
    Response body describing a site.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    timezone: str
