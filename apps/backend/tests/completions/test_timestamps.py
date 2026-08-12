from datetime import UTC, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import QuestCompletion
from tests.completions.helpers import (
    bearer,
    create_auth_client,
    create_campaign_and_quest,
    register,
)


def test_server_timestamps_and_valid_device_metadata_survive_exact_replay(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    observed_at = datetime.now(UTC) + timedelta(hours=23)
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        _, quest = create_campaign_and_quest(client, headers)
        payload = {
            "client_mutation_id": "d2000000-0000-4000-8000-000000000001",
            "expected_occurrence_version": 1,
            "device_observed_at": observed_at.isoformat(),
            "device_timezone_name": "America/Halifax",
        }
        first = client.post(
            f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete",
            headers=headers,
            json=payload,
        )
        replay = client.post(
            f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete",
            headers=headers,
            json=payload,
        )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()
    completion = first.json()["completion"]
    received_at = datetime.fromisoformat(completion["server_received_at"])
    processed_at = datetime.fromisoformat(completion["server_processed_at"])
    assert received_at.tzinfo is not None
    assert processed_at.tzinfo is not None
    assert processed_at >= received_at
    assert completion["completion_effective_date"] == str(
        received_at.astimezone(ZoneInfo("America/Halifax")).date()
    )
    assert datetime.fromisoformat(completion["device_observed_at"]) == observed_at
    assert completion["device_timezone_name"] == "America/Halifax"
    assert completion["client_time_valid"] is True


def test_implausible_device_time_is_flagged_but_does_not_control_acceptance(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    observed_at = datetime.now(UTC) + timedelta(hours=25)
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        _, quest = create_campaign_and_quest(client, headers)
        response = client.post(
            f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete",
            headers=headers,
            json={
                "client_mutation_id": "d2000000-0000-4000-8000-000000000002",
                "expected_occurrence_version": 1,
                "device_observed_at": observed_at.isoformat(),
                "device_timezone_name": "UTC",
            },
        )

    assert response.status_code == 200
    assert response.json()["completion"]["client_time_valid"] is False
    with auth_session_factory() as session:
        row = session.get(
            QuestCompletion,
            UUID(response.json()["completion"]["id"]),
        )
        assert row is not None
        assert row.device_observed_at == observed_at
        assert row.client_time_valid is False
        assert row.completion_effective_date != observed_at.date()


def test_malformed_timestamp_and_timezone_metadata_are_rejected(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        _, quest = create_campaign_and_quest(client, headers)
        base = {
            "client_mutation_id": "d2000000-0000-4000-8000-000000000003",
            "expected_occurrence_version": 1,
        }
        naive = client.post(
            f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete",
            headers=headers,
            json={**base, "device_observed_at": "2026-08-12T12:00:00"},
        )
        invalid_zone = client.post(
            f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete",
            headers=headers,
            json={
                **base,
                "device_timezone_name": "Not/A_Real_Timezone",
            },
        )

    assert naive.status_code == 422
    assert invalid_zone.status_code == 422
