"""
PostgreSQL engine and request-scoped session setup for the Atlas service.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from collections.abc import Generator

from sqlmodel import Session, create_engine

from atlas.settings import AtlasSettings

# ----- Consts ----- #

settings = AtlasSettings()
engine = create_engine(settings.database_url)

# ----- Functions ----- #


def get_session() -> Generator[Session, None, None]:
    """
    Open a session for one request and run the request in one transaction.

    :return: The request's session, inside a transaction that commits when the
        request succeeds and rolls back when it fails.
    """
    with Session(engine) as session:
        transaction = session.begin()
        try:
            yield session
        except Exception:
            transaction.rollback()
            raise

        transaction.commit()
