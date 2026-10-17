"""
PostgreSQL engine and request-scoped session setup for the Atlas service.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

import os
from collections.abc import Generator

from sqlmodel import Session, create_engine

# ----- Consts ----- #

DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://fieldops:fieldops@localhost:5432/fieldops",
)
engine = create_engine(DATABASE_URL)

# ----- Functions ----- #


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
