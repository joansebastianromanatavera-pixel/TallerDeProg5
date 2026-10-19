"""Integration tests for the Members CRUD API."""

from fastapi.testclient import TestClient

MEMBER = {"name": "Laura Gomez", "email": "laura@example.com", "phone": "+57 300 123 4567"}


def test_create_member_then_get_returns_it(client: TestClient) -> None:
    created = client.post("/api/v1/members", json=MEMBER)

    assert created.status_code == 201
    body = created.json()
    assert body["id"] > 0
    assert body["name"] == MEMBER["name"]
    assert body["email"] == MEMBER["email"]
    assert body["active"] is True

    fetched = client.get(f"/api/v1/members/{body['id']}")

    assert fetched.status_code == 200
    assert fetched.json() == body


def test_get_missing_member_returns_404_error_out(client: TestClient) -> None:
    response = client.get("/api/v1/members/9999")

    assert response.status_code == 404
    assert response.json() == {
        "error": "Not Found",
        "detail": "Member with id 9999 was not found.",
        "status": 404,
    }


def test_duplicate_email_returns_409(client: TestClient) -> None:
    assert client.post("/api/v1/members", json=MEMBER).status_code == 201

    duplicate = client.post("/api/v1/members", json={**MEMBER, "name": "Other Person"})

    assert duplicate.status_code == 409
    body = duplicate.json()
    assert body["status"] == 409
    assert body["error"] == "Conflict"
    assert MEMBER["email"] in body["detail"]
