"""
MongoDB database accessor tests for the documents service.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from orion.mongo import MONGO_DATABASE_NAME, get_documents_database


def test_get_documents_database_returns_configured_database():
    database = get_documents_database()

    assert database.name == MONGO_DATABASE_NAME
