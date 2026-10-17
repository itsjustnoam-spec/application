"""
Request and response schemas for sites.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ----- Classes ----- #


class InvalidTimezoneError(ValueError):
    """
    Raised when a timezone name is not a known IANA zone. Subclassing ValueError lets pydantic report it as a 422.
    """
    pass


class SiteInput(BaseModel):
    """
    The values a client sends to create or update a site.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=1, max_length=500)
    timezone: str = Field(min_length=1, max_length=64)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, timezone: str) -> str:
        """
        Accept only IANA timezone names.

        :param timezone: IANA name such as Europe/Berlin
        :return: the same name when it resolves
        :raises InvalidTimezoneError: when the name is not a known IANA timezone
        """
        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError as error:
            raise InvalidTimezoneError(
                f"{timezone} is not a valid IANA timezone.",
            ) from error

        return timezone


class SiteOut(BaseModel):
    """
    A site as the API returns it.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    timezone: str
    archived: bool
