from fastapi.testclient import TestClient

SITE_PAYLOAD = {
    "name": "HQ",
    "address": "1 Main Street",
    "timezone": "Europe/Berlin",
}


def test_get_session_successful_request_commits_its_writes(
    committing_api_client: TestClient,
):
    create_response = committing_api_client.post("/sites", json=SITE_PAYLOAD)

    read_response = committing_api_client.get(
        f"/sites/{create_response.json()['id']}",
    )

    assert read_response.status_code == 200
    assert read_response.json()["name"] == "HQ"


def test_get_session_failed_request_rolls_back_and_keeps_earlier_rows(
    committing_api_client: TestClient,
):
    committing_api_client.post("/sites", json=SITE_PAYLOAD)

    duplicate_response = committing_api_client.post(
        "/sites",
        json=SITE_PAYLOAD,
    )
    list_response = committing_api_client.get("/sites")

    assert duplicate_response.status_code == 409
    assert list_response.json()["total"] == 1
