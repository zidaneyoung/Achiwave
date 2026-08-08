from datetime import UTC, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import Quest, QuestOccurrence
from achiwave_backend.services.quests import _resolve_local_due
from tests.campaigns.helpers import bearer, create_auth_client, register


def _create_campaign(client, headers: dict[str, str]) -> dict[str, object]:
    response = client.post(
        "/api/v1/campaigns",
        headers=headers,
        json={
            "title": "Scheduled work",
            "client_mutation_id": "b9000000-0000-4000-8000-000000000001",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_due_date_uses_saved_timezone_and_preserves_occurrence_snapshot(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = _create_campaign(client, headers)
        payload = {
            "title": "Submit proposal",
            "difficulty": "medium",
            "due_local_datetime": "2099-12-31T23:00",
            "campaign_record_version": campaign["record_version"],
            "client_mutation_id": "b9000000-0000-4000-8000-000000000002",
        }
        created = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=headers,
            json=payload,
        )
        replay = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=headers,
            json=payload,
        )

    assert created.status_code == 201
    assert replay.status_code == 201
    assert replay.json() == created.json()
    result = created.json()
    assert result["due_at"] == "2100-01-01T03:00:00Z"
    assert result["timezone_name"] == "America/Halifax"
    assert result["due_status"] == "upcoming"
    assert result["occurrence"]["eligibility_expires_at"] == result["due_at"]
    assert result["occurrence"]["timezone_name"] == "America/Halifax"
    with auth_session_factory() as session:
        quest = session.get(Quest, UUID(result["id"]))
        occurrence = session.get(QuestOccurrence, UUID(result["occurrence"]["id"]))
        assert quest is not None and quest.due_at == occurrence.eligibility_expires_at
        assert quest.one_time_timezone_name == occurrence.timezone_name


def test_due_date_validates_local_shape_zone_and_future_on_server(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = _create_campaign(client, headers)
        invalid_inputs = [
            {"due_local_datetime": "2099-02-30T09:00"},
            {"due_local_datetime": "31 December 2099"},
            {"due_local_datetime": "2099-12-31T09:00", "timezone_name": "Mars/Olympus"},
            {"due_local_datetime": "2000-01-01T09:00"},
            {"timezone_name": "Asia/Tokyo"},
        ]
        for index, scheduling in enumerate(invalid_inputs, start=10):
            response = client.post(
                f"/api/v1/campaigns/{campaign['id']}/quests",
                headers=headers,
                json={
                    "title": "Invalid schedule",
                    "difficulty": "medium",
                    "campaign_record_version": campaign["record_version"],
                    "client_mutation_id": f"b9000000-0000-4000-8000-{index:012d}",
                    **scheduling,
                },
            )
            assert response.status_code == 422

        alternate = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=headers,
            json={
                "title": "Tokyo deadline",
                "difficulty": "medium",
                "due_local_datetime": "2099-12-31T23:00",
                "timezone_name": "Asia/Tokyo",
                "campaign_record_version": campaign["record_version"],
                "client_mutation_id": "b9000000-0000-4000-8000-000000000099",
            },
        )

    assert alternate.status_code == 201
    assert alternate.json()["due_at"] == "2099-12-31T14:00:00Z"
    assert alternate.json()["timezone_name"] == "Asia/Tokyo"


def test_due_status_is_server_derived_and_completed_snapshot_cannot_move(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = _create_campaign(client, headers)
        created = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=headers,
            json={
                "title": "Immutable deadline",
                "difficulty": "medium",
                "due_local_datetime": "2099-12-31T23:00",
                "campaign_record_version": campaign["record_version"],
                "client_mutation_id": "b9000000-0000-4000-8000-000000000100",
            },
        ).json()
        quest_id = UUID(created["id"])
        occurrence_id = UUID(created["occurrence"]["id"])
        with auth_session_factory.begin() as session:
            quest = session.get(Quest, quest_id)
            occurrence = session.get(QuestOccurrence, occurrence_id)
            assert quest is not None and occurrence is not None
            due_at = datetime.now(UTC) - timedelta(hours=1)
            quest.due_at = due_at
            occurrence.available_at = due_at - timedelta(days=1)
            occurrence.eligibility_expires_at = due_at

        overdue = client.get(f"/api/v1/quests/{quest_id}", headers=headers)
        with auth_session_factory.begin() as session:
            occurrence = session.get(QuestOccurrence, occurrence_id)
            assert occurrence is not None
            occurrence.occurrence_state = "completed"
            occurrence.completed_at = datetime.now(UTC)
        completed = client.get(f"/api/v1/quests/{quest_id}", headers=headers)
        rejected_move = client.patch(
            f"/api/v1/quests/{quest_id}",
            headers=headers,
            json={
                "title": "Do not move",
                "due_local_datetime": "2100-01-02T09:00",
                "record_version": created["record_version"],
                "client_mutation_id": "b9000000-0000-4000-8000-000000000101",
            },
        )

    assert overdue.status_code == 200
    assert overdue.json()["due_status"] == "overdue"
    assert completed.status_code == 200
    assert completed.json()["due_status"] == "unavailable"
    assert rejected_move.status_code == 422
    with auth_session_factory() as session:
        quest = session.get(Quest, quest_id)
        occurrence = session.get(QuestOccurrence, occurrence_id)
        assert quest is not None and occurrence is not None
        assert quest.title == "Immutable deadline"
        assert quest.due_at == occurrence.eligibility_expires_at


def test_due_resolution_follows_documented_dst_gap_and_overlap_rules() -> None:
    timezone = ZoneInfo("America/Halifax")
    assert _resolve_local_due("2027-03-14T02:30", timezone) == datetime(
        2027, 3, 14, 6, 0, tzinfo=UTC
    )
    assert _resolve_local_due("2027-11-07T01:30", timezone) == datetime(
        2027, 11, 7, 4, 30, tzinfo=UTC
    )
