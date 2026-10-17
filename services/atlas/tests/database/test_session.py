"""
Session dependency tests for the Atlas service.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from sqlmodel import Session

from atlas.database import get_session


def test_get_session_yields_session_instance():
    session_generator = get_session()

    session = next(session_generator)

    assert isinstance(session, Session)
    session_generator.close()
