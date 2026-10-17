"""
Paged list envelope shared by every list endpoint.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from pydantic import BaseModel

# ----- Classes ----- #


class Page[ItemT](BaseModel):
    items: list[ItemT]
    total: int
    limit: int
    offset: int
