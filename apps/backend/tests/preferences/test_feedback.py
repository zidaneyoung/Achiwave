from sqlalchemy.orm import Session, sessionmaker

from tests.auth.test_registration import create_auth_client, registration_payload


def bearer(token: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_sound_and_haptics_default_off_and_update_independently(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = client.post(
            "/api/v1/auth/register",
            json=registration_payload(),
        ).json()
        headers = bearer(registration["access_token"])
        initial = client.get("/api/v1/preferences", headers=headers)
        sound = client.patch(
            "/api/v1/preferences",
            headers=headers,
            json={"sound_enabled": True, "record_version": 1},
        )
        haptics = client.patch(
            "/api/v1/preferences",
            headers=headers,
            json={"haptics_enabled": True, "record_version": 2},
        )
        unchanged = client.patch(
            "/api/v1/preferences",
            headers=headers,
            json={"sound_enabled": True, "record_version": 3},
        )

    assert initial.status_code == 200
    assert initial.json()["sound_enabled"] is False
    assert initial.json()["haptics_enabled"] is False
    assert sound.status_code == 200
    assert sound.json()["sound_enabled"] is True
    assert sound.json()["haptics_enabled"] is False
    assert sound.json()["record_version"] == 2
    assert haptics.status_code == 200
    assert haptics.json()["sound_enabled"] is True
    assert haptics.json()["haptics_enabled"] is True
    assert haptics.json()["record_version"] == 3
    assert unchanged.status_code == 200
    assert unchanged.json()["record_version"] == 3


def test_feedback_preferences_reject_coercion_null_empty_and_stale_updates(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = client.post(
            "/api/v1/auth/register",
            json=registration_payload(),
        ).json()
        headers = bearer(registration["access_token"])
        accepted = client.patch(
            "/api/v1/preferences",
            headers=headers,
            json={"sound_enabled": True, "record_version": 1},
        )
        stale = client.patch(
            "/api/v1/preferences",
            headers=headers,
            json={"haptics_enabled": True, "record_version": 1},
        )
        coerced = client.patch(
            "/api/v1/preferences",
            headers=headers,
            json={"sound_enabled": "yes", "record_version": 2},
        )
        null_value = client.patch(
            "/api/v1/preferences",
            headers=headers,
            json={"haptics_enabled": None, "record_version": 2},
        )
        empty = client.patch(
            "/api/v1/preferences",
            headers=headers,
            json={"record_version": 2},
        )

    assert accepted.status_code == 200
    assert stale.status_code == 409
    assert stale.json()["code"] == "stale_record_version"
    for invalid in (coerced, null_value, empty):
        assert invalid.status_code == 422
        assert invalid.json()["code"] == "validation_error"
