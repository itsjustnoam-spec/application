from fastapi.testclient import TestClient
from sqlmodel import Session

from atlas.managers.sites import list_sites
from tests.utils import Environment, get_persisted_id


def test_list_sites_archived_rows_are_excluded(
    db_session: Session,
    env: Environment,
):
    sites, total = list_sites(db_session, 20, 0, None)

    assert [
        site.name
        for site in sites
    ] == [
        "Depot 100%",
        "Island Depot",
        "North Depot",
        "Quiet Depot",
        "South Depot",
    ]
    assert total == 5


def test_list_sites_query_matches_name_case_insensitively(
    db_session: Session,
    env: Environment,
):
    sites, _ = list_sites(db_session, 20, 0, "NORTH")

    assert [
        site.name
        for site in sites
    ] == [env.north_site.name]


def test_list_sites_query_with_percent_matches_it_literally(
    db_session: Session,
    env: Environment,
):
    sites, _ = list_sites(db_session, 20, 0, "%")

    assert [
        site.name
        for site in sites
    ] == [env.empty_site.name]


def test_list_sites_limit_and_offset_return_requested_page(
    db_session: Session,
    env: Environment,
):
    sites, total = list_sites(db_session, 2, 2, None)

    assert [
        site.name
        for site in sites
    ] == [
        "North Depot",
        "Quiet Depot",
    ]
    assert total == 5


def test_list_sites_api_returns_page_with_matching_sites(
    api_client: TestClient,
    env: Environment,
):
    response = api_client.get("/sites", params={"q": "north", "limit": 5})

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": get_persisted_id(env.north_site),
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
