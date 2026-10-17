"""
Validation tests for the asset type request schema.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

import pytest
from pydantic import ValidationError

from atlas.entities import AssetCategory
from atlas.schemas.asset_type import AssetTypeInput


@pytest.mark.parametrize("inspection_interval_days", [0, 3651])
def test_asset_type_input_interval_out_of_range_raises_validation_error(
    inspection_interval_days: int,
):
    with pytest.raises(ValidationError):
        AssetTypeInput(
            name="Pump",
            category=AssetCategory.MECHANICAL,
            inspection_interval_days=inspection_interval_days,
        )


def test_asset_type_input_unknown_category_raises_validation_error():
    with pytest.raises(ValidationError):
        AssetTypeInput.model_validate(
            {"name": "Pump", "category": "Plumbing", "inspection_interval_days": 30},
        )
