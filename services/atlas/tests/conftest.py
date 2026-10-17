from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlmodel import Session, SQLModel

import atlas.database
from atlas.database import get_session, settings
from atlas.entities import Asset, AssetCategory, AssetStatus, AssetType, Site
from atlas.main import app
from tests.utils import EARLIEST_TIMEZONE, Environment, get_persisted_id

TEST_DATABASE_NAME_SUFFIX = "_test"
TRUNCATE_ALL_TABLES = (
    "TRUNCATE TABLE asset, site, asset_type RESTART IDENTITY"
)


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


@pytest.fixture
def env(db_session: Session) -> Environment:
    north_site = Site(name="North Depot", address="1 Main Street", timezone="Europe/Berlin")
    south_site = Site(name="South Depot", address="2 Harbour Road", timezone="UTC")
    island_site = Site(name="Island Depot", address="3 Lagoon Way", timezone=EARLIEST_TIMEZONE)
    quiet_site = Site(name="Quiet Depot", address="4 Hill Lane", timezone="UTC")
    empty_site = Site(name="Depot 100%", address="5 Field Street", timezone="UTC")
    archived_site = Site(name="Old Depot", address="6 Dock Street", timezone="UTC", archived=True)
    pump = AssetType(name="Pump", category=AssetCategory.MECHANICAL, inspection_interval_days=30)
    fan = AssetType(name="Fan", category=AssetCategory.HVAC, inspection_interval_days=1)
    boiler = AssetType(name="Boiler", category=AssetCategory.MECHANICAL, inspection_interval_days=365)
    valve = AssetType(name="Valve", category=AssetCategory.SAFETY, inspection_interval_days=90)
    archived_asset_type = AssetType(
        name="Heater",
        category=AssetCategory.HVAC,
        inspection_interval_days=180,
        archived=True,
    )
    db_session.add_all(
        [
            north_site,
            south_site,
            island_site,
            quiet_site,
            empty_site,
            archived_site,
            pump,
            fan,
            boiler,
            valve,
            archived_asset_type,
        ],
    )
    db_session.flush()
    compressor = Asset(
        name="Compressor",
        serial_number="SN-1",
        site_id=get_persisted_id(north_site),
        asset_type_id=get_persisted_id(pump),
        status=AssetStatus.OPERATIONAL,
        installation_date=date(2026, 1, 1),
    )
    generator = Asset(
        name="Generator",
        serial_number="SN-2",
        site_id=get_persisted_id(south_site),
        asset_type_id=get_persisted_id(pump),
        status=AssetStatus.NEEDS_ATTENTION,
        installation_date=date(2026, 3, 1),
    )
    retired_conveyor = Asset(
        name="Conveyor",
        serial_number="SN-3",
        site_id=get_persisted_id(north_site),
        asset_type_id=get_persisted_id(pump),
        status=AssetStatus.RETIRED,
        installation_date=date(2025, 1, 1),
    )
    island_fan = Asset(
        name="Fan",
        serial_number="SN-4",
        site_id=get_persisted_id(island_site),
        asset_type_id=get_persisted_id(fan),
        status=AssetStatus.OPERATIONAL,
        installation_date=date(2026, 10, 16),
    )
    archived_boiler = Asset(
        name="Boiler",
        serial_number="SN-9",
        site_id=get_persisted_id(quiet_site),
        asset_type_id=get_persisted_id(boiler),
        status=AssetStatus.OPERATIONAL,
        installation_date=date(2026, 1, 1),
        archived=True,
    )
    db_session.add_all(
        [
            compressor,
            generator,
            retired_conveyor,
            island_fan,
            archived_boiler,
        ],
    )
    db_session.flush()
    return Environment(
        north_site=north_site,
        south_site=south_site,
        island_site=island_site,
        quiet_site=quiet_site,
        empty_site=empty_site,
        archived_site=archived_site,
        pump=pump,
        fan=fan,
        boiler=boiler,
        valve=valve,
        archived_asset_type=archived_asset_type,
        compressor=compressor,
        generator=generator,
        retired_conveyor=retired_conveyor,
        island_fan=island_fan,
        archived_boiler=archived_boiler,
    )
