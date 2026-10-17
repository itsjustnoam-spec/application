from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlmodel import Session, SQLModel

import atlas.database
from atlas.database import get_session, settings
from atlas.main import app

TEST_DATABASE_NAME_SUFFIX = "_test"
TRUNCATE_ALL_TABLES = "TRUNCATE TABLE site, asset_type RESTART IDENTITY"


class UnsafeTestDatabaseError(Exception):
    """
    Raised when the configured test database could be the application's database.
    """
    pass


def assert_safe_test_database(database_url: str | None):
    """
    Refuses any test database that is the application database or lacks the test suffix.

    :param database_url: SQLAlchemy URL of the database the tests are about to write to
    :raises UnsafeTestDatabaseError: when the URL is missing, is the application URL, or lacks the suffix
    """
    if database_url is None:
        raise UnsafeTestDatabaseError(
            "TEST_DATABASE_URL must be set in the service's .env file.",
        )

    if database_url == settings.database_url:
        raise UnsafeTestDatabaseError(
            "The test database must not be the application database.",
        )

    database_name = make_url(database_url).database
    if database_name is None or not database_name.endswith(TEST_DATABASE_NAME_SUFFIX):
        raise UnsafeTestDatabaseError(
            f"Test database name must end with {TEST_DATABASE_NAME_SUFFIX}.",
        )


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    assert_safe_test_database(settings.test_database_url)
    engine = create_engine(str(settings.test_database_url))
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
def committing_api_client(
    test_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    monkeypatch.setattr(atlas.database, "engine", test_engine)
    with TestClient(app) as test_client:
        yield test_client

    with test_engine.begin() as connection:
        connection.execute(text(TRUNCATE_ALL_TABLES))
