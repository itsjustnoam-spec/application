"""
Shared fixtures for the Atlas test suite, including the separate PostgreSQL test database.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

import os
from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlmodel import Session, SQLModel

from atlas.database import DATABASE_URL, get_session
from atlas.entities import AssetCategory, AssetType, Site
from atlas.main import app

# ----- Consts ----- #

DEFAULT_TEST_DATABASE_URL = (
    "postgresql+psycopg://fieldops:fieldops@localhost:5432/fieldops_test"
)
TEST_DATABASE_URL: str = os.environ.get(
    "TEST_DATABASE_URL",
    DEFAULT_TEST_DATABASE_URL,
)
TEST_DATABASE_NAME_SUFFIX = "_test"

# ----- Classes ----- #


class UnsafeTestDatabaseError(Exception):
    """
    Raised when the configured test database could be the application's database.
    """


# ----- Functions ----- #


def assert_safe_test_database(database_url: str):
    """
    Refuses any test database that is the application database or lacks the test suffix.

    :param database_url: SQLAlchemy URL of the database the tests are about to write to
    :raises UnsafeTestDatabaseError: when the URL is the application URL or its name lacks the suffix
    """
    database_name = make_url(database_url).database
    if database_url == DATABASE_URL:
        raise UnsafeTestDatabaseError(
            "The test database must not be the application database.",
        )

    if database_name is None or not database_name.endswith(TEST_DATABASE_NAME_SUFFIX):
        raise UnsafeTestDatabaseError(
            f"Test database name must end with {TEST_DATABASE_NAME_SUFFIX}.",
        )


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    assert_safe_test_database(TEST_DATABASE_URL)
    engine = create_engine(TEST_DATABASE_URL)
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield engine
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
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def api_client(db_session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_site(db_session: Session) -> Callable[..., Site]:
    def _make(
        name: str = "North Depot",
        address: str = "1 Main Street",
        timezone: str = "Europe/Berlin",
        archived: bool = False,
    ) -> Site:
        site = Site(
            name=name,
            address=address,
            timezone=timezone,
            archived=archived,
        )
        db_session.add(site)
        db_session.commit()
        db_session.refresh(site)
        return site

    return _make


@pytest.fixture
def make_asset_type(db_session: Session) -> Callable[..., AssetType]:
    def _make(
        name: str = "Pump",
        category: AssetCategory = AssetCategory.MECHANICAL,
        inspection_interval_days: int = 30,
        archived: bool = False,
    ) -> AssetType:
        asset_type = AssetType(
            name=name,
            category=category,
            inspection_interval_days=inspection_interval_days,
            archived=archived,
        )
        db_session.add(asset_type)
        db_session.commit()
        db_session.refresh(asset_type)
        return asset_type

    return _make
