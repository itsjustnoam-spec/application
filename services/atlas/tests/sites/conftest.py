from collections.abc import Callable

import pytest
from sqlmodel import Session

from atlas.entities import Site


@pytest.fixture
def make_site(db_session: Session) -> Callable[..., Site]:
    def _make(
        name: str = "North Depot",
        address: str = "1 Main Street",
        timezone: str = "Europe/Berlin",
        archived: bool = False,
    ) -> Site:
        site = Site(
            name=name,
            address=address,
            timezone=timezone,
            archived=archived,
        )
        db_session.add(site)
        db_session.commit()
        db_session.refresh(site)
        return site

    return _make
