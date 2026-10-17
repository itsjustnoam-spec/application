"""
Domain exceptions raised by the Atlas managers and mapped to HTTP responses in main.py.

:author: Noam
:date: 17/10/26
"""

# ----- Classes ----- #


class EntityNotFoundError(Exception):
    """
    Raised when the requested row does not exist or is soft-deleted.
    """


class DuplicateNameError(Exception):
    """
    Raised when a name collides with a live or soft-deleted row of the same table.
    """
