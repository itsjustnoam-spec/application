"""
Site table model for the Atlas service.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from sqlmodel import Field, SQLModel

# ----- Classes ----- #


class Site(SQLModel, table=True):
    """
    A physical location where assets are installed.
    """

    __tablename__ = "sites"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    address: str = Field(max_length=255)
    timezone: str = Field(max_length=64)
    is_deleted: bool = Field(default=False)
