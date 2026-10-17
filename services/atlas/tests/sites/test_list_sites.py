from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.entities import Site
from atlas.managers.sites import list_sites


def test_list_sites_archived_rows_are_excluded(
    db_session: Session,
    make_site: Callable[..., Site],
):
    make_site(name="North Depot")
    make_site(name="Old Depot", archived=True)

    sites, total = list_sites(db_session, 20, 0, None)

    assert [
        site.name
        for site in sites
    ] == ["North Depot"]
    assert total == 1


def test_list_sites_query_matches_name_case_insensitively(
    db_session: Session,
    make_site: Callable[..., Site],
):
    make_site(name="North Depot")
    make_site(name="South Depot")

    sites, _ = list_sites(db_session, 20, 0, "NORTH")

    assert [
        site.name
        for site in sites
    ] == ["North Depot"]


def test_list_sites_query_with_percent_matches_it_literally(
    db_session: Session,
    make_site: Callable[..., Site],
):
    make_site(name="Depot 100%")
    make_site(name="Depot 1000")

    sites, _ = list_sites(db_session, 20, 0, "100%")

    assert [
        site.name
        for site in sites
    ] == ["Depot 100%"]


def test_list_sites_limit_and_offset_return_requested_page(
    db_session: Session,
    make_site: Callable[..., Site],
):
    make_site(name="A Depot")
    make_site(name="B Depot")
    make_site(name="C Depot")

    sites, total = list_sites(db_session, 2, 2, None)

    assert [
        site.name
        for site in sites
    ] == ["C Depot"]
    assert total == 3


def test_list_sites_api_returns_page_with_matching_sites(
    api_client: TestClient,
    make_site: Callable[..., Site],
):
    make_site(name="North Depot")
    make_site(name="South Depot")

    response = api_client.get("/sites", params={"q": "north", "limit": 5})

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": response.json()["items"][0]["id"],
                "name": "North Depot",
                "address": "1 Main Street",
                "timezone": "Europe/Berlin",
                "archived": False,
            },
        ],
        "total": 1,
        "limit": 5,
        "offset": 0,
    }


def test_list_sites_api_limit_above_100_returns_422(api_client: TestClient):
    response = api_client.get("/sites", params={"limit": 101})

    assert response.status_code == 422
