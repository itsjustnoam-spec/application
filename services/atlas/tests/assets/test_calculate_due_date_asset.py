from datetime import UTC, date, datetime

import pytest

from atlas.entities import AssetStatus
from atlas.managers.due_dates import is_overdue, next_inspection_due


def test_next_inspection_due_installed_asset_adds_interval_to_installation_date():
    due_date = next_inspection_due(
        date(2026, 1, 1),
        30,
        AssetStatus.OPERATIONAL,
    )

    assert due_date == date(2026, 1, 31)


def test_next_inspection_due_uses_last_inspection_when_given():
    due_date = next_inspection_due(
        date(2026, 1, 1),
        30,
        AssetStatus.OPERATIONAL,
        last_inspection_date=date(2026, 3, 1),
    )

    assert due_date == date(2026, 3, 31)


@pytest.mark.parametrize("status", [AssetStatus.OUT_OF_SERVICE, AssetStatus.RETIRED])
def test_next_inspection_due_out_of_service_returns_none(status: AssetStatus):
    due_date = next_inspection_due(date(2026, 1, 1), 30, status)

    assert due_date is None


def test_is_overdue_due_yesterday_in_site_timezone_returns_true():
    now = datetime(2026, 10, 16, 15, 30, tzinfo=UTC)

    overdue = is_overdue(date(2026, 10, 16), "Asia/Tokyo", now=now)

    assert overdue is True


def test_is_overdue_due_today_in_site_timezone_returns_false():
    now = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)

    overdue = is_overdue(date(2026, 10, 17), "UTC", now=now)

    assert overdue is False


def test_is_overdue_missing_due_date_returns_false():
    overdue = is_overdue(None, "UTC")

    assert overdue is False
