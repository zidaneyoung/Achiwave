from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import RegisteredDevice
from tests.auth.test_registration import (
    PASSWORD,
    create_auth_client,
    registration_payload,
)


def bearer(token: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register(client, **overrides: object) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/register",
        json=registration_payload(**overrides),
    )
    assert response.status_code == 201
    return response.json()


def test_current_device_registration_updates_metadata_without_duplication(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    payload = registration_payload()["installation"]
    assert isinstance(payload, dict)
    updated = {**payload, "app_version": "1.1.0", "build_version": "2"}
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        first = client.put(
            "/api/v1/devices/current",
            headers=bearer(registration["access_token"]),
            json=updated,
        )
        repeated = client.put(
            "/api/v1/devices/current",
            headers=bearer(registration["access_token"]),
            json=updated,
        )

    assert first.status_code == 200
    assert repeated.status_code == 200
    assert first.json()["id"] == registration["device_id"]
    assert first.json()["is_current"] is True
    assert first.json()["app_version"] == "1.1.0"
    assert repeated.json()["record_version"] == first.json()["record_version"]
    with auth_session_factory() as session:
        device_count = session.scalar(select(func.count()).select_from(RegisteredDevice))
    assert device_count == 1


def test_current_device_registration_rejects_mismatched_installation(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    payload = registration_payload()["installation"]
    assert isinstance(payload, dict)
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        response = client.put(
            "/api/v1/devices/current",
            headers=bearer(registration["access_token"]),
            json={**payload, "installation_id": str(uuid4())},
        )

    assert response.status_code == 409
    assert response.json()["code"] == "invalid_device_context"


def test_device_list_is_owner_scoped_and_marks_current_device(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        first = register(client)
        other_installation = {
            **registration_payload()["installation"],
            "installation_id": str(uuid4()),
        }
        register(
            client,
            email="other@example.com",
            password=PASSWORD,
            installation=other_installation,
        )
        response = client.get(
            "/api/v1/devices",
            headers=bearer(first["access_token"]),
        )

    assert response.status_code == 200
    devices = response.json()["devices"]
    assert len(devices) == 1
    assert devices[0]["id"] == first["device_id"]
    assert devices[0]["is_current"] is True
    assert "installation_id" not in devices[0]


def test_device_endpoints_require_authentication(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        listing = client.get("/api/v1/devices")
        update = client.put(
            "/api/v1/devices/current",
            json=registration_payload()["installation"],
        )

    assert listing.status_code == 401
    assert update.status_code == 401
