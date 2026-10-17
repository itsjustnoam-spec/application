"""
Next inspection due dates for assets, and whether they are overdue in the site's timezone.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from atlas.entities import AssetStatus

# ----- Consts ----- #

STATUSES_WITHOUT_DUE_DATE = frozenset(
    {
        AssetStatus.OUT_OF_SERVICE,
        AssetStatus.RETIRED,
    },
)

# ----- Functions ----- #


def next_inspection_due(
    installation_date: date,
    inspection_interval_days: int,
    status: AssetStatus,
    last_inspection_date: date | None = None,
) -> date | None:
    """
    Calculate when an asset is next due for inspection.

    The due date counts from the last inspection when there is one, otherwise from the installation date.

    :param installation_date: The day the asset was installed.
    :param inspection_interval_days: How many days pass between inspections.
    :param status: The asset's status; retired and out of service assets have no due date.
    :param last_inspection_date: The day of the last inspection, or None when there has been none.
    :return: The due date, or None when the status has no due date.
    """
    if status in STATUSES_WITHOUT_DUE_DATE:
        return None

    base_date = installation_date if last_inspection_date is None else last_inspection_date
    return base_date + timedelta(days=inspection_interval_days)


def is_overdue(
    due_date: date | None,
    site_timezone: str,
    now: datetime | None = None,
) -> bool:
    """
    Check whether a due date has passed in the site's timezone, where a due date of today is not overdue.

    :param due_date: The next due date, or None when there is none.
    :param site_timezone: The IANA timezone name of the site.
    :param now: The current moment, or None to use the real clock.
    :return: Whether the due date is before today in the site's timezone.
    """
    if due_date is None:
        return False

    current_moment = now
    if current_moment is None:
        current_moment = datetime.now(ZoneInfo("UTC"))

    today = current_moment.astimezone(ZoneInfo(site_timezone)).date()
    return due_date < today
