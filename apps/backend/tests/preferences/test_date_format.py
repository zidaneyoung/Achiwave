import pytest
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import UserPreference
from tests.auth.test_registration import create_auth_client, registration_payload


DATE_FORMATS = [
    "system",
    "day_month_year",
    "month_day_year",
    "year_month_day",
]


def bearer(token: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("date_format", DATE_FORMATS)
def test_date_format_values_round_trip_and_increment_on_change(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
    date_format: str,
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = client.post(
            "/api/v1/auth/register",
            json=registration_payload(),
        ).json()
        response = client.patch(
            "/api/v1/preferences",
            headers=bearer(registration["access_token"]),
            json={"date_format": date_format, "record_version": 1},
        )

    assert response.status_code == 200
    assert response.json()["date_format"] == date_format
    expected_version = 1 if date_format == "system" else 2
    assert response.json()["record_version"] == expected_version


def test_date_format_rejects_invalid_api_and_database_values(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = client.post(
            "/api/v1/auth/register",
            json=registration_payload(),
        ).json()
        response = client.patch(
            "/api/v1/preferences",
            headers=bearer(registration["access_token"]),
            json={"date_format": "regional_guess", "record_version": 1},
        )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    with auth_session_factory() as session:
        with pytest.raises(IntegrityError):
            session.execute(
                update(UserPreference).values(date_format="regional_guess")
            )
            session.commit()
        session.rollback()


def test_date_format_rejects_stale_preference_version(
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
            json={"date_format": "day_month_year", "record_version": 1},
        )
        stale = client.patch(
            "/api/v1/preferences",
            headers=headers,
            json={"date_format": "year_month_day", "record_version": 1},
        )

    assert accepted.status_code == 200
    assert stale.status_code == 409
    assert stale.json()["code"] == "stale_record_version"
