from datetime import UTC, datetime

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


def test_timezone_read_and_prospective_update_use_server_time_and_versions(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    before_update = datetime.now(UTC)
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        initial = client.get("/api/v1/preferences", headers=headers)
        updated = client.patch(
            "/api/v1/preferences/timezone",
            headers=headers,
            json={"timezone_name": "Asia/Tokyo", "record_version": 1},
        )
        unchanged = client.patch(
            "/api/v1/preferences/timezone",
            headers=headers,
            json={"timezone_name": "Asia/Tokyo", "record_version": 2},
        )
    after_update = datetime.now(UTC)

    assert initial.status_code == 200
    assert initial.json()["timezone_name"] == "America/Halifax"
    assert updated.status_code == 200
    payload = updated.json()
    assert payload["timezone_name"] == "Asia/Tokyo"
    assert payload["timezone_version"] == 2
    assert payload["record_version"] == 2
    effective_at = datetime.fromisoformat(payload["timezone_effective_at"])
    assert before_update <= effective_at <= after_update
    assert unchanged.status_code == 200
    assert unchanged.json()["timezone_version"] == 2
    assert unchanged.json()["record_version"] == 2
    assert unchanged.json()["timezone_effective_at"] == payload["timezone_effective_at"]


def test_timezone_update_rejects_stale_record_version(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        accepted = client.patch(
            "/api/v1/preferences/timezone",
            headers=headers,
            json={"timezone_name": "Europe/Paris", "record_version": 1},
        )
        stale = client.patch(
            "/api/v1/preferences/timezone",
            headers=headers,
            json={"timezone_name": "Asia/Tokyo", "record_version": 1},
        )

    assert accepted.status_code == 200
    assert stale.status_code == 409
    assert stale.json()["code"] == "stale_record_version"


@pytest.mark.parametrize(
    "timezone_name",
    ["AST", "-04:00", "UTC+04:00", "Etc/GMT+4", "Not/AZone", " America/Halifax"],
)
def test_timezone_update_rejects_offsets_abbreviations_and_unknown_zones(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
    timezone_name: str,
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        response = client.patch(
            "/api/v1/preferences/timezone",
            headers=bearer(registration["access_token"]),
            json={"timezone_name": timezone_name, "record_version": 1},
        )

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_timezone"


def test_preference_access_is_authenticated_owner_scoped_and_rejects_unknown_fields(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        first = register(client)
        second = register(
            client,
            email="other@example.com",
            timezone_name="Asia/Tokyo",
            installation={
                **registration_payload()["installation"],
                "installation_id": "20000000-0000-4000-8000-000000000002",
            },
        )
        first_result = client.get(
            "/api/v1/preferences",
            headers=bearer(first["access_token"]),
        )
        second_result = client.get(
            "/api/v1/preferences",
            headers=bearer(second["access_token"]),
        )
        unauthenticated = client.get("/api/v1/preferences")
        unknown = client.patch(
            "/api/v1/preferences/timezone",
            headers=bearer(first["access_token"]),
            json={
                "timezone_name": "UTC",
                "record_version": 1,
                "user_id": second["user"]["id"],
            },
        )

    assert first_result.status_code == 200
    assert first_result.json()["timezone_name"] == "America/Halifax"
    assert second_result.status_code == 200
    assert second_result.json()["timezone_name"] == "Asia/Tokyo"
    assert unauthenticated.status_code == 401
    assert unknown.status_code == 422
    assert unknown.json()["code"] == "validation_error"
