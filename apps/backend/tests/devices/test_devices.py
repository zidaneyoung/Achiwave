from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import DeviceSession, RegisteredDevice
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


def login(client, installation: dict[str, object]) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "Person@example.com",
            "password": PASSWORD,
            "installation": installation,
        },
    )
    assert response.status_code == 200
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


def test_session_list_returns_safe_owned_metadata(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    installation = registration_payload()["installation"]
    assert isinstance(installation, dict)
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        login(client, installation)
        response = client.get(
            "/api/v1/sessions",
            headers=bearer(registration["access_token"]),
        )

    assert response.status_code == 200
    sessions = response.json()["sessions"]
    assert len(sessions) == 2
    assert sum(item["is_current"] for item in sessions) == 1
    assert all(item["device_label"] == "Android device" for item in sessions)
    serialized = response.text.lower()
    assert "credential" not in serialized
    assert "token" not in serialized


def test_revoke_other_session_is_idempotent_and_keeps_caller_active(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    installation = registration_payload()["installation"]
    assert isinstance(installation, dict)
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        caller = register(client)
        target = login(client, installation)
        first = client.post(
            f"/api/v1/sessions/{target['session_id']}/revoke",
            headers=bearer(caller["access_token"]),
        )
        repeated = client.post(
            f"/api/v1/sessions/{target['session_id']}/revoke",
            headers=bearer(caller["access_token"]),
        )
        caller_still_active = client.get(
            "/api/v1/users/me",
            headers=bearer(caller["access_token"]),
        )
        rejected_refresh = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": target["refresh_token"],
                "installation": installation,
            },
        )

    assert first.status_code == 200
    assert first.json()["current_session_revoked"] is False
    assert first.json()["already_inactive"] is False
    assert repeated.status_code == 200
    assert repeated.json()["already_inactive"] is True
    assert repeated.json()["revoked_at"] == first.json()["revoked_at"]
    assert caller_still_active.status_code == 200
    assert rejected_refresh.status_code == 401
    assert rejected_refresh.json()["code"] == "session_revoked"


def test_revoke_device_revokes_every_device_session_in_one_request(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    second_installation = {
        **registration_payload()["installation"],
        "installation_id": str(uuid4()),
    }
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        caller = register(client)
        target_one = login(client, second_installation)
        target_two = login(client, second_installation)
        first = client.post(
            f"/api/v1/devices/{target_one['device_id']}/revoke",
            headers=bearer(caller["access_token"]),
        )
        repeated = client.post(
            f"/api/v1/devices/{target_one['device_id']}/revoke",
            headers=bearer(caller["access_token"]),
        )
        caller_still_active = client.get(
            "/api/v1/users/me",
            headers=bearer(caller["access_token"]),
        )

    assert first.status_code == 200
    assert first.json()["current_session_revoked"] is False
    assert first.json()["already_inactive"] is False
    assert repeated.status_code == 200
    assert repeated.json()["already_inactive"] is True
    assert caller_still_active.status_code == 200
    with auth_session_factory() as session:
        target_states = list(
            session.scalars(
                select(DeviceSession.session_state).where(
                    DeviceSession.id.in_(
                        [target_one["session_id"], target_two["session_id"]]
                    )
                )
            )
        )
        caller_state = session.scalar(
            select(DeviceSession.session_state).where(
                DeviceSession.id == caller["session_id"]
            )
        )
    assert target_states == ["revoked", "revoked"]
    assert caller_state == "active"


def test_revoke_current_device_signals_sign_out_and_invalidates_access(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        response = client.post(
            f"/api/v1/devices/{registration['device_id']}/revoke",
            headers=bearer(registration["access_token"]),
        )
        rejected = client.get(
            "/api/v1/users/me",
            headers=bearer(registration["access_token"]),
        )

    assert response.status_code == 200
    assert response.json()["current_session_revoked"] is True
    assert response.json()["revoked_at"] is not None
    assert rejected.status_code == 401
    assert rejected.json()["code"] == "session_revoked"


def test_cross_user_revocation_targets_use_not_found_behavior(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    other_installation = {
        **registration_payload()["installation"],
        "installation_id": str(uuid4()),
    }
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        caller = register(client)
        other = register(
            client,
            email="other@example.com",
            password=PASSWORD,
            installation=other_installation,
        )
        device_response = client.post(
            f"/api/v1/devices/{other['device_id']}/revoke",
            headers=bearer(caller["access_token"]),
        )
        session_response = client.post(
            f"/api/v1/sessions/{other['session_id']}/revoke",
            headers=bearer(caller["access_token"]),
        )

    assert device_response.status_code == 404
    assert device_response.json()["code"] == "not_found"
    assert session_response.status_code == 404
    assert session_response.json()["code"] == "not_found"
