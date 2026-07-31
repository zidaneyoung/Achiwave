import pytest
from sqlalchemy.orm import Session, sessionmaker

from tests.auth.test_registration import create_auth_client, registration_payload


def bearer(token: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register(client, **overrides: object) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/register",
        json=registration_payload(**overrides),
    )
    assert response.status_code == 201
    return response.json()


def test_profile_read_and_semantic_update_are_owner_scoped(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        first = register(client)
        second = register(
            client,
            email="other@example.com",
            installation={
                **registration_payload()["installation"],
                "installation_id": "20000000-0000-4000-8000-000000000002",
            },
        )
        initial = client.get(
            "/api/v1/users/me",
            headers=bearer(first["access_token"]),
        )
        updated = client.patch(
            "/api/v1/users/me",
            headers=bearer(first["access_token"]),
            json={"display_name": "Zoë Young", "record_version": 1},
        )
        unchanged = client.patch(
            "/api/v1/users/me",
            headers=bearer(first["access_token"]),
            json={"display_name": "Zoë Young", "record_version": 2},
        )
        other = client.get(
            "/api/v1/users/me",
            headers=bearer(second["access_token"]),
        )

    assert initial.status_code == 200
    assert initial.json()["display_name"] is None
    assert updated.status_code == 200
    assert updated.json()["email"] == "Person@example.com"
    assert updated.json()["display_name"] == "Zoë Young"
    assert updated.json()["record_version"] == 2
    assert unchanged.status_code == 200
    assert unchanged.json()["record_version"] == 2
    assert other.status_code == 200
    assert other.json()["email"] == "other@example.com"
    assert other.json()["display_name"] is None


def test_profile_update_rejects_stale_version_and_email_fields(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        accepted = client.patch(
            "/api/v1/users/me",
            headers=headers,
            json={"display_name": "First Name", "record_version": 1},
        )
        stale = client.patch(
            "/api/v1/users/me",
            headers=headers,
            json={"display_name": "Second Name", "record_version": 1},
        )
        email_change = client.patch(
            "/api/v1/users/me",
            headers=headers,
            json={
                "display_name": "Second Name",
                "email": "replacement@example.com",
                "record_version": 2,
            },
        )

    assert accepted.status_code == 200
    assert stale.status_code == 409
    assert stale.json()["code"] == "stale_record_version"
    assert email_change.status_code == 422
    assert email_change.json()["code"] == "validation_error"


@pytest.mark.parametrize(
    "display_name",
    ["", " leading", "trailing ", "two  spaces", "bad/name", "emoji 😀", "x" * 81],
)
def test_profile_update_rejects_invalid_display_names(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
    display_name: str,
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        response = client.patch(
            "/api/v1/users/me",
            headers=bearer(registration["access_token"]),
            json={"display_name": display_name, "record_version": 1},
        )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
