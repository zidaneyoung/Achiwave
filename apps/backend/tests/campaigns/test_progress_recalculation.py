from datetime import UTC, datetime, time
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import (
    Campaign,
    ProgressEvent,
    Quest,
    QuestOccurrence,
    QuestRecurrence,
    XpLedgerEntry,
)
from achiwave_backend.services.campaigns import _derived_campaign_state
from tests.completions.helpers import (
    bearer,
    create_auth_client,
    create_campaign_and_quest,
    register,
)


def test_obligation_changes_and_completion_lifecycle_recalculate_campaign(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        owner = register(client)
        headers = bearer(owner["access_token"])
        _, first_quest = create_campaign_and_quest(client, headers, title="First")
        campaign_id = first_quest["campaign_id"]
        first_completion_payload = {
            "client_mutation_id": "d7000000-0000-4000-8000-000000000001",
            "expected_occurrence_version": 1,
        }
        first_completed = client.post(
            f"/api/v1/quest-occurrences/{first_quest['occurrence']['id']}/complete",
            headers=headers,
            json=first_completion_payload,
        )
        first_replay = client.post(
            f"/api/v1/quest-occurrences/{first_quest['occurrence']['id']}/complete",
            headers=headers,
            json=first_completion_payload,
        )
        assert first_completed.status_code == 200
        assert first_replay.json() == first_completed.json()
        assert first_completed.json()["campaign"]["status"] == "completed"

        second_payload = {
            "title": "New unfinished obligation",
            "difficulty": "medium",
            "reward_xp": 20,
            "campaign_record_version": first_completed.json()["campaign"][
                "record_version"
            ],
            "client_mutation_id": "d7000000-0000-4000-8000-000000000002",
        }
        second_created = client.post(
            f"/api/v1/campaigns/{campaign_id}/quests",
            headers=headers,
            json=second_payload,
        )
        second_replay = client.post(
            f"/api/v1/campaigns/{campaign_id}/quests",
            headers=headers,
            json=second_payload,
        )
        assert second_created.status_code == 201
        assert second_replay.status_code == 201
        assert second_replay.json()["id"] == second_created.json()["id"]
        assert second_created.json()["campaign_status"] == "active"
        second_quest = second_created.json()

        archived = client.post(
            f"/api/v1/quests/{second_quest['id']}/archive",
            headers=headers,
            json={
                "client_mutation_id": "d7000000-0000-4000-8000-000000000003",
                "record_version": second_quest["record_version"],
            },
        )
        assert archived.status_code == 200
        assert archived.json()["campaign_status"] == "completed"
        restored = client.post(
            f"/api/v1/quests/{second_quest['id']}/restore",
            headers=headers,
            json={
                "client_mutation_id": "d7000000-0000-4000-8000-000000000004",
                "record_version": archived.json()["record_version"],
            },
        )
        assert restored.status_code == 200
        assert restored.json()["campaign_status"] == "active"

        second_completed = client.post(
            f"/api/v1/quest-occurrences/{second_quest['occurrence']['id']}/complete",
            headers=headers,
            json={
                "client_mutation_id": "d7000000-0000-4000-8000-000000000005",
                "expected_occurrence_version": 1,
            },
        )
        assert second_completed.status_code == 200
        assert second_completed.json()["campaign"]["status"] == "completed"
        second_reversed = client.post(
            "/api/v1/quest-completions/"
            f"{second_completed.json()['completion']['id']}/reverse",
            headers=headers,
            json={
                "client_mutation_id": "d7000000-0000-4000-8000-000000000006",
                "expected_occurrence_version": 2,
                "reason": "user_correction",
            },
        )
        assert second_reversed.status_code == 200
        assert second_reversed.json()["campaign"]["status"] == "active"
        second_recompleted = client.post(
            f"/api/v1/quest-occurrences/{second_quest['occurrence']['id']}/complete",
            headers=headers,
            json={
                "client_mutation_id": "d7000000-0000-4000-8000-000000000007",
                "expected_occurrence_version": 3,
            },
        )
        second_recompletion_replay = client.post(
            f"/api/v1/quest-occurrences/{second_quest['occurrence']['id']}/complete",
            headers=headers,
            json={
                "client_mutation_id": "d7000000-0000-4000-8000-000000000007",
                "expected_occurrence_version": 3,
            },
        )
        assert second_recompleted.status_code == 200
        assert second_recompletion_replay.json() == second_recompleted.json()
        assert second_recompleted.json()["campaign"]["status"] == "completed"

    with auth_session_factory() as session:
        transitions = session.scalars(
            select(ProgressEvent.event_type)
            .where(
                ProgressEvent.user_id == UUID(str(owner["user"]["id"])),
                ProgressEvent.event_type.in_(
                    ("campaign_completed", "campaign_reopened")
                ),
            )
            .order_by(ProgressEvent.event_sequence)
        ).all()
        assert transitions == [
            "campaign_completed",
            "campaign_reopened",
            "campaign_completed",
            "campaign_reopened",
            "campaign_completed",
            "campaign_reopened",
            "campaign_completed",
        ]
        assert session.scalar(select(func.count()).select_from(XpLedgerEntry)) == 0


def test_archiving_only_obligation_leaves_empty_campaign_active(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        owner = register(client)
        headers = bearer(owner["access_token"])
        _, quest = create_campaign_and_quest(client, headers)
        archived = client.post(
            f"/api/v1/quests/{quest['id']}/archive",
            headers=headers,
            json={
                "client_mutation_id": "d7000000-0000-4000-8000-000000000008",
                "record_version": quest["record_version"],
            },
        )
        campaign = client.get(
            f"/api/v1/campaigns/{quest['campaign_id']}", headers=headers
        )

    assert archived.status_code == 200
    assert archived.json()["campaign_status"] == "active"
    assert campaign.status_code == 200
    assert campaign.json()["status"] == "active"
    assert campaign.json()["completed_at"] is None


def test_empty_finite_and_open_ended_predicates_use_postgresql_rows(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    now = datetime.now(UTC)
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        owner = register(client)
    owner_id = UUID(str(owner["user"]["id"]))
    with auth_session_factory.begin() as session:
        empty = Campaign(user_id=owner_id, title="Empty")
        recurring = Campaign(user_id=owner_id, title="Recurring")
        session.add_all([empty, recurring])
        session.flush()
        quest = Quest(
            user_id=owner_id,
            campaign_id=recurring.id,
            quest_type="recurring",
            title="Repeat",
        )
        session.add(quest)
        session.flush()
        rule = QuestRecurrence(
            quest_id=quest.id,
            user_id=owner_id,
            campaign_id=recurring.id,
            quest_type="recurring",
            frequency="daily",
            start_local_date=now.date(),
            scheduled_local_time=time(9),
            timezone_name="UTC",
        )
        session.add_all(
            [
                rule,
                QuestOccurrence(
                    user_id=owner_id,
                    campaign_id=recurring.id,
                    quest_id=quest.id,
                    quest_type="recurring",
                    occurrence_state="completed",
                    occurrence_local_date=now.date(),
                    scheduled_local_time=time(9),
                    timezone_name="UTC",
                    timezone_data_version="system",
                    rule_version=1,
                    available_at=now,
                    completed_at=now,
                    reward_xp=0,
                ),
            ]
        )
        session.flush()
        assert _derived_campaign_state(session, empty, now) == "active"
        assert _derived_campaign_state(session, recurring, now) == "active"
        rule.max_occurrences = 1
        session.flush()
        assert _derived_campaign_state(session, recurring, now) == "completed"
