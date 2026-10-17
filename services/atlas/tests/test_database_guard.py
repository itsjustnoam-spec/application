"""
Tests for the guard that stops the suite from writing to the application database.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

import pytest

from tests.conftest import UnsafeTestDatabaseError, assert_safe_test_database


def test_assert_safe_test_database_application_name_raises_error():
    application_url = "postgresql+psycopg://fieldops:fieldops@localhost:5432/fieldops"

    with pytest.raises(UnsafeTestDatabaseError):
        assert_safe_test_database(application_url)


def test_assert_safe_test_database_test_name_passes():
    test_url = "postgresql+psycopg://fieldops:fieldops@localhost:5432/fieldops_test"

    result = assert_safe_test_database(test_url)

    assert result is None
