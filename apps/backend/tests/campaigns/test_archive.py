from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import (
    Campaign,
    ClientMutation,
    ProgressEvent,
    Quest,
    QuestOccurrence,
)
from tests.campaigns.helpers import bearer, create_auth_client, register, registration_payload

MUTATION_ID = "90000000-0000-4000-8000-000000000009"


def test_campaign_archive_is_versioned_replay_safe_and_preserves_children(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        created = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={
                "title": "Archive me",
                "client_mutation_id": "90000000-0000-4000-8000-000000000001",
            },
        ).json()
        with auth_session_factory.begin() as session:
            quest = Quest(
                user_id=UUID(str(registration["user"]["id"])),
                campaign_id=UUID(created["id"]),
                quest_type="one_time",
                title="Preserved quest",
                reward_xp=10,
            )
            session.add(quest)
            session.flush()
            occurrence = QuestOccurrence(
                user_id=quest.user_id,
                campaign_id=quest.campaign_id,
                quest_id=quest.id,
                quest_type="one_time",
                occurrence_state="available",
                occurrence_local_date=date.today(),
                timezone_name="UTC",
                timezone_data_version="system",
                rule_version=1,
                available_at=datetime.now(UTC),
                reward_xp=10,
            )
            session.add(occurrence)
            session.flush()
            quest_id = quest.id
            occurrence_id = occurrence.id
        payload = {"record_version": 1, "client_mutation_id": MUTATION_ID}
        archived = client.post(
            f"/api/v1/campaigns/{created['id']}/archive",
            headers=headers,
            json=payload,
        )
        replay = client.post(
            f"/api/v1/campaigns/{created['id']}/archive",
            headers=headers,
            json=payload,
        )

    assert archived.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == archived.json()
    assert archived.json()["status"] == "archived"
    assert archived.json()["record_version"] == 2
    assert archived.json()["archived_at"] is not None
    with auth_session_factory() as session:
        quest = session.get(Quest, quest_id)
        occurrence = session.get(QuestOccurrence, occurrence_id)
        event_count = session.scalar(
            select(func.count())
            .select_from(ProgressEvent)
            .where(ProgressEvent.event_type == "campaign_archived")
        )
        mutation_count = session.scalar(
            select(func.count())
            .select_from(ClientMutation)
            .where(ClientMutation.operation_type == "campaign_archive")
        )
    assert quest is not None and quest.definition_state == "active"
    assert occurrence is not None and occurrence.occurrence_state == "available"
    assert event_count == 1
    assert mutation_count == 1


def test_campaign_archive_accepts_completed_and_distinct_already_applied_without_side_effect(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        with auth_session_factory.begin() as session:
            campaign = Campaign(
                user_id=UUID(str(registration["user"]["id"])),
                title="Completed",
                campaign_state="completed",
                completed_at=datetime.now(UTC),
            )
            session.add(campaign)
            session.flush()
            campaign_id = campaign.id
        first = client.post(
            f"/api/v1/campaigns/{campaign_id}/archive",
            headers=headers,
            json={"record_version": 1, "client_mutation_id": MUTATION_ID},
        )
        already = client.post(
            f"/api/v1/campaigns/{campaign_id}/archive",
            headers=headers,
            json={
                "record_version": 2,
                "client_mutation_id": "90000000-0000-4000-8000-000000000002",
            },
        )

    assert first.status_code == 200
    assert already.status_code == 200
    assert already.json()["record_version"] == 2
    with auth_session_factory() as session:
        assert session.scalar(
            select(func.count())
            .select_from(ProgressEvent)
            .where(ProgressEvent.event_type == "campaign_archived")
        ) == 1


def test_campaign_archive_returns_stale_canonical_state_and_hides_cross_user(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        first = register(client)
        second = register(
            client,
            email="archive@example.com",
            installation={
                **dict(registration_payload()["installation"]),
                "installation_id": "90000000-0000-4000-8000-000000000003",
            },
        )
        private = client.post(
            "/api/v1/campaigns",
            headers=bearer(second["access_token"]),
            json={
                "title": "Private",
                "client_mutation_id": "90000000-0000-4000-8000-000000000004",
            },
        ).json()
        edited = client.patch(
            f"/api/v1/campaigns/{private['id']}",
            headers=bearer(second["access_token"]),
            json={
                "title": "Newer",
                "record_version": 1,
                "client_mutation_id": "90000000-0000-4000-8000-000000000005",
            },
        )
        stale = client.post(
            f"/api/v1/campaigns/{private['id']}/archive",
            headers=bearer(second["access_token"]),
            json={"record_version": 1, "client_mutation_id": MUTATION_ID},
        )
        cross_user = client.post(
            f"/api/v1/campaigns/{private['id']}/archive",
            headers=bearer(first["access_token"]),
            json={"record_version": 2, "client_mutation_id": MUTATION_ID},
        )

    assert edited.status_code == 200
    assert stale.status_code == 409
    assert stale.json()["current"]["title"] == "Newer"
    assert cross_user.status_code == 404
