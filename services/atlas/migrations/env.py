"""
Alembic environment that applies Atlas schema migrations to PostgreSQL.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from alembic import context
from sqlmodel import SQLModel

import atlas.entities  # noqa: F401  # registers tables on SQLModel.metadata
from atlas.database import engine, settings

# ----- Consts ----- #

TARGET_METADATA = SQLModel.metadata

# ----- Functions ----- #


def run_migrations_offline():
    context.configure(
        url=settings.database_url,
        target_metadata=TARGET_METADATA,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=TARGET_METADATA,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
