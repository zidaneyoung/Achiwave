import pytest
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import UserPreference
from tests.auth.test_registration import create_auth_client, registration_payload


def bearer(token: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("reduced_motion", ["system", "reduce", "allow"])
def test_reduced_motion_values_round_trip_with_system_default(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
    reduced_motion: str,
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = client.post(
            "/api/v1/auth/register",
            json=registration_payload(),
        ).json()
        headers = bearer(registration["access_token"])
        initial = client.get("/api/v1/preferences", headers=headers)
        response = client.patch(
            "/api/v1/preferences",
            headers=headers,
            json={"reduced_motion": reduced_motion, "record_version": 1},
        )

    assert initial.status_code == 200
    assert initial.json()["reduced_motion"] == "system"
    assert response.status_code == 200
    assert response.json()["reduced_motion"] == reduced_motion
    expected_version = 1 if reduced_motion == "system" else 2
    assert response.json()["record_version"] == expected_version


def test_reduced_motion_rejects_invalid_api_database_and_stale_values(
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
            json={"reduced_motion": "reduce", "record_version": 1},
        )
        stale = client.patch(
            "/api/v1/preferences",
            headers=headers,
            json={"reduced_motion": "allow", "record_version": 1},
        )
        invalid = client.patch(
            "/api/v1/preferences",
            headers=headers,
            json={"reduced_motion": "disabled", "record_version": 2},
        )

    assert accepted.status_code == 200
    assert stale.status_code == 409
    assert stale.json()["code"] == "stale_record_version"
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "validation_error"
    with auth_session_factory() as session:
        with pytest.raises(IntegrityError):
            session.execute(
                update(UserPreference).values(reduced_motion="disabled")
            )
            session.commit()
        session.rollback()
