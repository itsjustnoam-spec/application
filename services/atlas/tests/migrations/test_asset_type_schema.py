"""
Schema tests for the asset type table on the test database.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from sqlalchemy import Engine, text


def test_asset_type_partial_unique_index_exists_on_active_names(test_engine: Engine):
    with test_engine.connect() as connection:
        index_definition: str = connection.execute(
            text(
                "SELECT indexdef FROM pg_indexes "
                "WHERE indexname = 'uq_asset_type_name_active'",
            ),
        ).scalar_one()

    assert "WHERE (archived = false)" in index_definition
