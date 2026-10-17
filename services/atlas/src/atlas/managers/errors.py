"""
Domain errors raised by the managers and mapped to HTTP responses in main.py.

:author: Noam
:date: 17/10/26
"""

# ----- Classes ----- #


class EntityNotFoundError(Exception):
    """
    Raised when the requested row does not exist or is archived.
    """
    pass


class DuplicateNameError(Exception):
    """
    Raised when an active row already uses the requested name.
    """
    pass
