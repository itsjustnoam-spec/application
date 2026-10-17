"""
Site table model for physical locations where assets are installed.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from sqlalchemy import Index, text
from sqlmodel import Field, SQLModel

# ----- Classes ----- #


class Site(SQLModel, table=True):
    """
    A physical location with an address and the timezone used for its schedules.
    """
    __tablename__ = "site"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    address: str = Field(max_length=500)
    timezone: str = Field(max_length=64)
    archived: bool = Field(default=False)

    __table_args__ = (
        Index(
            "uq_site_name_active",
            "name",
            unique=True,
            postgresql_where=text("archived = false"),
        ),
    )
