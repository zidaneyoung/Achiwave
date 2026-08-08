from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import func, null, select, update
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import (
    Campaign,
    ClientMutation,
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


def test_campaign_lifecycle_replay_returns_original_materialized_results(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    archive_mutation_id = UUID("a0000000-0000-4000-8000-000000000011")
    restore_mutation_id = UUID("a0000000-0000-4000-8000-000000000012")
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        created = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={
                "title": "Durable lifecycle",
                "client_mutation_id": "a0000000-0000-4000-8000-000000000010",
            },
        ).json()
        archive_payload = {
            "record_version": created["record_version"],
            "client_mutation_id": str(archive_mutation_id),
        }
        archived = client.post(
            f"/api/v1/campaigns/{created['id']}/archive",
            headers=headers,
            json=archive_payload,
        )
        archived_result = archived.json()
        restore_payload = {
            "record_version": archived_result["record_version"],
            "client_mutation_id": str(restore_mutation_id),
        }
        restored = client.post(
            f"/api/v1/campaigns/{created['id']}/restore",
            headers=headers,
            json=restore_payload,
        )
        restored_result = restored.json()
        delayed_archive_replay = client.post(
            f"/api/v1/campaigns/{created['id']}/archive",
            headers=headers,
            json=archive_payload,
        )
        rearchived = client.post(
            f"/api/v1/campaigns/{created['id']}/archive",
            headers=headers,
            json={
                "record_version": restored_result["record_version"],
                "client_mutation_id": "a0000000-0000-4000-8000-000000000013",
            },
        )
        delayed_restore_replay = client.post(
            f"/api/v1/campaigns/{created['id']}/restore",
            headers=headers,
            json=restore_payload,
        )
        current = client.get(
            f"/api/v1/campaigns/{created['id']}",
            headers=headers,
        )

    assert archived.status_code == 200
    assert restored.status_code == 200
    assert delayed_archive_replay.status_code == 200
    assert delayed_archive_replay.json() == archived_result
    assert rearchived.status_code == 200
    assert delayed_restore_replay.status_code == 200
    assert delayed_restore_replay.json() == restored_result
    assert current.status_code == 200
    assert current.json()["status"] == "archived"
    assert current.json()["record_version"] == rearchived.json()["record_version"]
    with auth_session_factory() as session:
        archive_mutation = session.scalar(
            select(ClientMutation).where(
                ClientMutation.client_mutation_id == archive_mutation_id
            )
        )
        restore_mutation = session.scalar(
            select(ClientMutation).where(
                ClientMutation.client_mutation_id == restore_mutation_id
            )
        )
        lifecycle_mutations = session.scalar(
            select(func.count())
            .select_from(ClientMutation)
            .where(
                ClientMutation.operation_type.in_(
                    ("campaign_archive", "campaign_restore")
                )
            )
        )
        archived_events = session.scalar(
            select(func.count())
            .select_from(ProgressEvent)
            .where(ProgressEvent.event_type == "campaign_archived")
        )
        restored_events = session.scalar(
            select(func.count())
            .select_from(ProgressEvent)
            .where(ProgressEvent.event_type == "campaign_restored")
        )

    assert archive_mutation is not None
    assert archive_mutation.result_payload == archived_result
    assert restore_mutation is not None
    assert restore_mutation.result_payload == restored_result
    assert lifecycle_mutations == 3
    assert archived_events == 2
    assert restored_events == 1


def test_campaign_lifecycle_legacy_null_result_falls_back_without_new_effects(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    archive_mutation_id = UUID("a0000000-0000-4000-8000-000000000021")
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        created = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={
                "title": "Legacy replay",
                "client_mutation_id": "a0000000-0000-4000-8000-000000000020",
            },
        ).json()
        archive_payload = {
            "record_version": created["record_version"],
            "client_mutation_id": str(archive_mutation_id),
        }
        archived = client.post(
            f"/api/v1/campaigns/{created['id']}/archive",
            headers=headers,
            json=archive_payload,
        ).json()
        with auth_session_factory.begin() as session:
            updated = session.execute(
                update(ClientMutation)
                .where(
                    ClientMutation.client_mutation_id == archive_mutation_id
                )
                .values(result_payload=null())
            )
            assert updated.rowcount == 1
        restored = client.post(
            f"/api/v1/campaigns/{created['id']}/restore",
            headers=headers,
            json={
                "record_version": archived["record_version"],
                "client_mutation_id": "a0000000-0000-4000-8000-000000000022",
            },
        )
        legacy_replay = client.post(
            f"/api/v1/campaigns/{created['id']}/archive",
            headers=headers,
            json=archive_payload,
        )

    assert restored.status_code == 200
    assert legacy_replay.status_code == 200
    assert legacy_replay.json() == restored.json()
    with auth_session_factory() as session:
        assert session.scalar(
            select(func.count())
            .select_from(ProgressEvent)
            .where(ProgressEvent.event_type == "campaign_archived")
        ) == 1
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
