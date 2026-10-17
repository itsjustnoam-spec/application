"""
Integration tests for the asset type manager against the test database.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from collections.abc import Callable

import pytest
from sqlmodel import Session

from atlas.entities import AssetCategory, AssetType
from atlas.managers.asset_types import (
    archive_asset_type,
    create_asset_type,
    list_asset_types,
    read_asset_type,
    update_asset_type,
)
from atlas.managers.errors import DuplicateNameError, EntityNotFoundError
from atlas.schemas.asset_type import AssetTypeInput

MISSING_ASSET_TYPE_ID = 9999


def test_list_asset_types_excludes_archived_rows(
    db_session: Session,
    make_asset_type: Callable[..., AssetType],
):
    make_asset_type(name="Pump")
    make_asset_type(name="Valve", archived=True)

    asset_types, total = list_asset_types(db_session, 20, 0, None)

    assert [asset_type.name for asset_type in asset_types] == ["Pump"]
    assert total == 1


def test_list_asset_types_query_matches_name_case_insensitively(
    db_session: Session,
    make_asset_type: Callable[..., AssetType],
):
    make_asset_type(name="Pump")
    make_asset_type(name="Valve")

    asset_types, _ = list_asset_types(db_session, 20, 0, "pump")

    assert [asset_type.name for asset_type in asset_types] == ["Pump"]


def test_read_asset_type_missing_id_raises_entity_not_found_error(db_session: Session):
    with pytest.raises(EntityNotFoundError, match="Asset type not found"):
        read_asset_type(db_session, MISSING_ASSET_TYPE_ID)


def test_create_asset_type_duplicate_active_name_raises_duplicate_name_error(
    db_session: Session,
    make_asset_type: Callable[..., AssetType],
):
    make_asset_type(name="Pump")

    with pytest.raises(
        DuplicateNameError,
        match="An asset type with this name already exists",
    ):
        create_asset_type(
            db_session,
            AssetTypeInput(
                name="Pump",
                category=AssetCategory.HVAC,
                inspection_interval_days=60,
            ),
        )


def test_create_asset_type_archived_name_is_reusable(
    db_session: Session,
    make_asset_type: Callable[..., AssetType],
):
    make_asset_type(name="Pump", archived=True)

    created_asset_type = create_asset_type(
        db_session,
        AssetTypeInput(
            name="Pump",
            category=AssetCategory.HVAC,
            inspection_interval_days=60,
        ),
    )

    assert created_asset_type.archived is False


def test_update_asset_type_replaces_fields(
    db_session: Session,
    make_asset_type: Callable[..., AssetType],
):
    asset_type = make_asset_type()
    assert asset_type.id is not None

    updated_asset_type = update_asset_type(
        db_session,
        asset_type.id,
        AssetTypeInput(
            name="Compressor",
            category=AssetCategory.SAFETY,
            inspection_interval_days=90,
        ),
    )

    assert (
        updated_asset_type.name,
        updated_asset_type.category,
        updated_asset_type.inspection_interval_days,
    ) == ("Compressor", AssetCategory.SAFETY, 90)


def test_update_asset_type_rename_to_taken_name_raises_duplicate_name_error(
    db_session: Session,
    make_asset_type: Callable[..., AssetType],
):
    make_asset_type(name="Pump")
    other_asset_type = make_asset_type(name="Valve")
    assert other_asset_type.id is not None

    with pytest.raises(
        DuplicateNameError,
        match="An asset type with this name already exists",
    ):
        update_asset_type(
            db_session,
            other_asset_type.id,
            AssetTypeInput(
                name="Pump",
                category=AssetCategory.MECHANICAL,
                inspection_interval_days=30,
            ),
        )


def test_update_asset_type_missing_id_raises_entity_not_found_error(db_session: Session):
    with pytest.raises(EntityNotFoundError, match="Asset type not found"):
        update_asset_type(
            db_session,
            MISSING_ASSET_TYPE_ID,
            AssetTypeInput(
                name="Pump",
                category=AssetCategory.MECHANICAL,
                inspection_interval_days=30,
            ),
        )


def test_archive_asset_type_sets_archived_and_keeps_row(
    db_session: Session,
    make_asset_type: Callable[..., AssetType],
):
    asset_type = make_asset_type()
    assert asset_type.id is not None

    archive_asset_type(db_session, asset_type.id)
    stored_asset_type = db_session.get(AssetType, asset_type.id)

    assert stored_asset_type is not None
    assert stored_asset_type.archived is True


def test_archive_asset_type_missing_id_raises_entity_not_found_error(db_session: Session):
    with pytest.raises(EntityNotFoundError, match="Asset type not found"):
        archive_asset_type(db_session, MISSING_ASSET_TYPE_ID)
