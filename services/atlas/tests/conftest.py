"""
Shared fixtures for the Atlas test suite.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from atlas.database import get_session
from atlas.entities.asset_type import AssetType  # noqa: F401
from atlas.entities.site import Site  # noqa: F401
from atlas.main import app

# ----- Consts ----- #

TEST_DATABASE_URL: str = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://fieldops:fieldops@localhost:5432/fieldops_test",
)

# ----- Functions ----- #


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    engine = create_engine(TEST_DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Iterator[Session]:
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def db_client(db_session: Session) -> Iterator[TestClient]:
    def override_get_session() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
