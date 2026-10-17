"""
Validation tests for the site request schema.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

import pytest
from pydantic import ValidationError

from atlas.schemas.site import SiteInput


def test_site_input_unknown_timezone_raises_invalid_timezone_error():
    with pytest.raises(
        ValidationError,
        match="Mars/Olympus is not a valid IANA timezone.",
    ):
        SiteInput(name="HQ", address="1 Main Street", timezone="Mars/Olympus")


def test_site_input_valid_iana_timezone_keeps_value():
    site_input = SiteInput(name="HQ", address="1 Main Street", timezone="Europe/Berlin")

    assert site_input.timezone == "Europe/Berlin"


def test_site_input_blank_name_raises_validation_error():
    with pytest.raises(ValidationError):
        SiteInput(name="", address="1 Main Street", timezone="Europe/Berlin")


def test_site_input_blank_address_raises_validation_error():
    with pytest.raises(ValidationError):
        SiteInput(name="HQ", address="", timezone="Europe/Berlin")


def test_site_input_whitespace_only_name_raises_validation_error():
    with pytest.raises(ValidationError):
        SiteInput(name="   ", address="1 Main Street", timezone="Europe/Berlin")
