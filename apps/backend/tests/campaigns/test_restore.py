from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import (
    Campaign,
    ProgressEvent,
    Quest,
    QuestOccurrence,
    XpLedgerEntry,
)
from tests.campaigns.helpers import bearer, create_auth_client, register, registration_payload


def test_campaign_restore_is_versioned_replay_safe_and_empty_stays_active(
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
                "title": "Restore me",
                "client_mutation_id": "a0000000-0000-4000-8000-000000000001",
            },
        ).json()
        archived = client.post(
            f"/api/v1/campaigns/{created['id']}/archive",
            headers=headers,
            json={
                "record_version": 1,
                "client_mutation_id": "a0000000-0000-4000-8000-000000000002",
            },
        ).json()
        payload = {
            "record_version": archived["record_version"],
            "client_mutation_id": "a0000000-0000-4000-8000-000000000003",
        }
        restored = client.post(
            f"/api/v1/campaigns/{created['id']}/restore",
            headers=headers,
            json=payload,
        )
        replay = client.post(
            f"/api/v1/campaigns/{created['id']}/restore",
            headers=headers,
            json=payload,
        )

    assert restored.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == restored.json()
    assert restored.json()["status"] == "active"
    assert restored.json()["record_version"] == 3
    assert restored.json()["restored_at"] is not None
    with auth_session_factory() as session:
        assert session.scalar(
            select(func.count())
            .select_from(ProgressEvent)
            .where(ProgressEvent.event_type == "campaign_restored")
        ) == 1


def test_campaign_restore_rederives_completed_without_rewarding_again(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    completed_at = datetime.now(UTC)
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        with auth_session_factory.begin() as session:
            campaign = Campaign(
                user_id=UUID(str(registration["user"]["id"])),
                title="Already completed",
                campaign_state="completed",
                completion_reason="all_obligations_completed",
                completed_at=completed_at,
            )
            session.add(campaign)
            session.flush()
            quest = Quest(
                user_id=campaign.user_id,
                campaign_id=campaign.id,
                quest_type="one_time",
                title="Done",
                reward_xp=20,
            )
            session.add(quest)
            session.flush()
            session.add(
                QuestOccurrence(
                    user_id=campaign.user_id,
                    campaign_id=campaign.id,
                    quest_id=quest.id,
                    quest_type="one_time",
                    occurrence_state="completed",
                    occurrence_local_date=date.today(),
                    timezone_name="UTC",
                    timezone_data_version="system",
                    rule_version=1,
                    available_at=completed_at,
                    completed_at=completed_at,
                    reward_xp=20,
                )
            )
            campaign_id = campaign.id
        archived = client.post(
            f"/api/v1/campaigns/{campaign_id}/archive",
            headers=headers,
            json={
                "record_version": 1,
                "client_mutation_id": "a0000000-0000-4000-8000-000000000004",
            },
        ).json()
        restored = client.post(
            f"/api/v1/campaigns/{campaign_id}/restore",
            headers=headers,
            json={
                "record_version": archived["record_version"],
                "client_mutation_id": "a0000000-0000-4000-8000-000000000005",
            },
        )

    assert restored.status_code == 200
    assert restored.json()["status"] == "completed"
    assert datetime.fromisoformat(restored.json()["completed_at"]) == completed_at
    with auth_session_factory() as session:
        assert session.scalar(select(func.count()).select_from(XpLedgerEntry)) == 0
        assert session.scalar(
            select(func.count())
            .select_from(ProgressEvent)
            .where(ProgressEvent.event_type == "campaign_restored")
        ) == 1


def test_campaign_restore_rejects_invalid_structure_and_hides_cross_user(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        first = register(client)
        second = register(
            client,
            email="restore@example.com",
            installation={
                **dict(registration_payload()["installation"]),
                "installation_id": "a0000000-0000-4000-8000-000000000006",
            },
        )
        with auth_session_factory.begin() as session:
            campaign = Campaign(
                user_id=UUID(str(second["user"]["id"])),
                title="Broken",
                campaign_state="archived",
                archived_at=datetime.now(UTC),
            )
            session.add(campaign)
            session.flush()
            session.add(
                Quest(
                    user_id=campaign.user_id,
                    campaign_id=campaign.id,
                    quest_type="one_time",
                    title="Missing occurrence",
                )
            )
            campaign_id = campaign.id
        payload = {
            "record_version": 1,
            "client_mutation_id": "a0000000-0000-4000-8000-000000000007",
        }
        invalid = client.post(
            f"/api/v1/campaigns/{campaign_id}/restore",
            headers=bearer(second["access_token"]),
            json=payload,
        )
        cross_user = client.post(
            f"/api/v1/campaigns/{campaign_id}/restore",
            headers=bearer(first["access_token"]),
            json=payload,
        )

    assert invalid.status_code == 409
    assert invalid.json()["code"] == "campaign_restore_invalid"
    assert cross_user.status_code == 404
