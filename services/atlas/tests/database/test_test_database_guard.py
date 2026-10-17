import pytest

from atlas.database import settings
from tests.conftest import UnsafeTestDatabaseError, assert_safe_test_database

NOT_A_TEST_DATABASE_URL = "postgresql+psycopg://fieldops@localhost:5432/other"
TEST_DATABASE_URL = "postgresql+psycopg://fieldops@localhost:5432/fieldops_test"


@pytest.mark.parametrize("database_url,expected_message", [
    (None, "TEST_DATABASE_URL must be set"),
    (settings.database_url, "must not be the application database"),
    (NOT_A_TEST_DATABASE_URL, "must end with _test"),
])
def test_assert_safe_test_database_unsafe_url_raises_unsafe_error(
    database_url: str | None,
    expected_message: str,
):
    with pytest.raises(UnsafeTestDatabaseError, match=expected_message):
        assert_safe_test_database(database_url)


def test_assert_safe_test_database_test_url_passes():
    result = assert_safe_test_database(TEST_DATABASE_URL)

    assert result is None
