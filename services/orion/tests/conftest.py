"""
Shared fixtures for the documents test suite.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from orion.main import app

# ----- Functions ----- #


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
