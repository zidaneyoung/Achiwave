from datetime import UTC, datetime
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


def _create_campaign_and_quest(client, headers: dict[str, str]) -> tuple[dict, dict]:
    campaign = client.post(
        "/api/v1/campaigns",
        headers=headers,
        json={
            "title": "Lifecycle",
            "client_mutation_id": "d0000000-0000-4000-8000-000000000001",
        },
    ).json()
    quest = client.post(
        f"/api/v1/campaigns/{campaign['id']}/quests",
        headers=headers,
        json={
            "title": "Preserve me",
            "difficulty": "hard",
            "reward_xp": 20,
            "campaign_record_version": 1,
            "client_mutation_id": "d0000000-0000-4000-8000-000000000002",
        },
    ).json()
    return campaign, quest


def test_quest_archive_and_restore_are_replay_safe_and_preserve_occurrence(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign, quest = _create_campaign_and_quest(client, headers)
        archive_payload = {
            "record_version": 1,
            "client_mutation_id": "d0000000-0000-4000-8000-000000000003",
        }
        archived = client.post(
            f"/api/v1/quests/{quest['id']}/archive", headers=headers, json=archive_payload
        )
        archive_replay = client.post(
            f"/api/v1/quests/{quest['id']}/archive", headers=headers, json=archive_payload
        )
        already_archived = client.post(
            f"/api/v1/quests/{quest['id']}/archive",
            headers=headers,
            json={
                "record_version": 2,
                "client_mutation_id": "d0000000-0000-4000-8000-00000000000e",
            },
        )
        hidden = client.get(f"/api/v1/campaigns/{campaign['id']}", headers=headers)
        historical = client.get(
            f"/api/v1/campaigns/{campaign['id']}?include_archived_quests=true",
            headers=headers,
        )
        restore_payload = {
            "record_version": archived.json()["record_version"],
            "client_mutation_id": "d0000000-0000-4000-8000-000000000004",
        }
        restored = client.post(
            f"/api/v1/quests/{quest['id']}/restore", headers=headers, json=restore_payload
        )
        restore_replay = client.post(
            f"/api/v1/quests/{quest['id']}/restore", headers=headers, json=restore_payload
        )
        already_restored = client.post(
            f"/api/v1/quests/{quest['id']}/restore",
            headers=headers,
            json={
                "record_version": 3,
                "client_mutation_id": "d0000000-0000-4000-8000-00000000000f",
            },
        )

    assert archived.status_code == 200
    assert archive_replay.json() == archived.json()
    assert already_archived.json() == archived.json()
    assert archived.json()["definition_state"] == "archived"
    assert archived.json()["record_version"] == 2
    assert archived.json()["campaign_record_version"] == 3
    assert archived.json()["occurrence"] == quest["occurrence"]
    assert hidden.json()["quests"] == []
    assert historical.json()["quests"][0]["id"] == quest["id"]
    assert restored.status_code == 200
    assert restore_replay.json() == restored.json()
    assert already_restored.json() == restored.json()
    assert restored.json()["definition_state"] == "active"
    assert restored.json()["record_version"] == 3
    assert restored.json()["campaign_record_version"] == 4
    assert restored.json()["occurrence"] == quest["occurrence"]
    with auth_session_factory() as session:
        occurrence = session.get(QuestOccurrence, UUID(quest["occurrence"]["id"]))
        assert occurrence is not None and occurrence.occurrence_state == "available"
        assert session.scalar(select(func.count()).select_from(XpLedgerEntry)) == 0
        for event_type in ("quest_archived", "quest_restored"):
            assert session.scalar(
                select(func.count())
                .select_from(ProgressEvent)
                .where(ProgressEvent.event_type == event_type)
            ) == 1


def test_quest_lifecycle_recalculates_campaign_from_authoritative_obligations(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign, first = _create_campaign_and_quest(client, headers)
        second = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=headers,
            json={
                "title": "Unfinished",
                "difficulty": "easy",
                "reward_xp": 0,
                "campaign_record_version": first["campaign_record_version"],
                "client_mutation_id": "d0000000-0000-4000-8000-000000000005",
            },
        ).json()
        with auth_session_factory.begin() as session:
            occurrence = session.get(QuestOccurrence, UUID(first["occurrence"]["id"]))
            assert occurrence is not None
            occurrence.occurrence_state = "completed"
            occurrence.completed_at = datetime.now(UTC)
        archived = client.post(
            f"/api/v1/quests/{second['id']}/archive",
            headers=headers,
            json={
                "record_version": 1,
                "client_mutation_id": "d0000000-0000-4000-8000-000000000006",
            },
        )
        restored = client.post(
            f"/api/v1/quests/{second['id']}/restore",
            headers=headers,
            json={
                "record_version": archived.json()["record_version"],
                "client_mutation_id": "d0000000-0000-4000-8000-000000000007",
            },
        )

    assert archived.status_code == 200
    assert archived.json()["campaign_status"] == "completed"
    assert restored.status_code == 200
    assert restored.json()["campaign_status"] == "active"
    with auth_session_factory() as session:
        stored_campaign = session.get(Campaign, UUID(campaign["id"]))
        assert stored_campaign is not None and stored_campaign.campaign_state == "active"
        assert session.scalar(
            select(func.count())
            .select_from(ProgressEvent)
            .where(ProgressEvent.event_type == "campaign_completed")
        ) == 1
        assert session.scalar(
            select(func.count())
            .select_from(ProgressEvent)
            .where(ProgressEvent.event_type == "campaign_reopened")
        ) == 1


def test_quest_lifecycle_replay_survives_inverse_and_parent_transitions(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    archive_mutation_id = UUID("d0000000-0000-4000-8000-000000000030")
    restore_mutation_id = UUID("d0000000-0000-4000-8000-000000000031")
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign, quest = _create_campaign_and_quest(client, headers)
        archive_payload = {
            "record_version": quest["record_version"],
            "client_mutation_id": str(archive_mutation_id),
        }
        archived = client.post(
            f"/api/v1/quests/{quest['id']}/archive",
            headers=headers,
            json=archive_payload,
        )
        archived_result = archived.json()
        restore_payload = {
            "record_version": archived_result["record_version"],
            "client_mutation_id": str(restore_mutation_id),
        }
        restored = client.post(
            f"/api/v1/quests/{quest['id']}/restore",
            headers=headers,
            json=restore_payload,
        )
        restored_result = restored.json()
        delayed_archive_replay = client.post(
            f"/api/v1/quests/{quest['id']}/archive",
            headers=headers,
            json=archive_payload,
        )
        rearchived = client.post(
            f"/api/v1/quests/{quest['id']}/archive",
            headers=headers,
            json={
                "record_version": restored_result["record_version"],
                "client_mutation_id": "d0000000-0000-4000-8000-000000000032",
            },
        )
        delayed_restore_replay = client.post(
            f"/api/v1/quests/{quest['id']}/restore",
            headers=headers,
            json=restore_payload,
        )
        parent_archived = client.post(
            f"/api/v1/campaigns/{campaign['id']}/archive",
            headers=headers,
            json={
                "record_version": rearchived.json()["campaign_record_version"],
                "client_mutation_id": "d0000000-0000-4000-8000-000000000033",
            },
        )
        replay_archive_after_parent = client.post(
            f"/api/v1/quests/{quest['id']}/archive",
            headers=headers,
            json=archive_payload,
        )
        replay_restore_after_parent = client.post(
            f"/api/v1/quests/{quest['id']}/restore",
            headers=headers,
            json=restore_payload,
        )
        current = client.get(f"/api/v1/quests/{quest['id']}", headers=headers)

    assert archived.status_code == 200
    assert restored.status_code == 200
    assert delayed_archive_replay.status_code == 200
    assert delayed_archive_replay.json() == archived_result
    assert rearchived.status_code == 200
    assert delayed_restore_replay.status_code == 200
    assert delayed_restore_replay.json() == restored_result
    assert parent_archived.status_code == 200
    assert replay_archive_after_parent.status_code == 200
    assert replay_archive_after_parent.json() == archived_result
    assert replay_restore_after_parent.status_code == 200
    assert replay_restore_after_parent.json() == restored_result
    assert current.status_code == 200
    assert current.json()["definition_state"] == "archived"
    assert current.json()["campaign_status"] == "archived"
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
                    (
                        "one_time_quest_archive",
                        "one_time_quest_restore",
                        "campaign_archive",
                    )
                )
            )
        )
        event_counts = {
            event_type: session.scalar(
                select(func.count())
                .select_from(ProgressEvent)
                .where(ProgressEvent.event_type == event_type)
            )
            for event_type in (
                "quest_archived",
                "quest_restored",
                "campaign_archived",
            )
        }

    assert archive_mutation is not None
    assert archive_mutation.result_payload == archived_result
    assert restore_mutation is not None
    assert restore_mutation.result_payload == restored_result
    assert lifecycle_mutations == 4
    assert event_counts == {
        "quest_archived": 2,
        "quest_restored": 1,
        "campaign_archived": 1,
    }


def test_quest_lifecycle_legacy_null_result_uses_current_parent_boundary(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    archive_mutation_id = UUID("d0000000-0000-4000-8000-000000000040")
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign, quest = _create_campaign_and_quest(client, headers)
        archive_payload = {
            "record_version": quest["record_version"],
            "client_mutation_id": str(archive_mutation_id),
        }
        archived = client.post(
            f"/api/v1/quests/{quest['id']}/archive",
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
            f"/api/v1/quests/{quest['id']}/restore",
            headers=headers,
            json={
                "record_version": archived["record_version"],
                "client_mutation_id": "d0000000-0000-4000-8000-000000000041",
            },
        )
        legacy_replay = client.post(
            f"/api/v1/quests/{quest['id']}/archive",
            headers=headers,
            json=archive_payload,
        )
        parent_archived = client.post(
            f"/api/v1/campaigns/{campaign['id']}/archive",
            headers=headers,
            json={
                "record_version": restored.json()["campaign_record_version"],
                "client_mutation_id": "d0000000-0000-4000-8000-000000000042",
            },
        )
        legacy_replay_after_parent = client.post(
            f"/api/v1/quests/{quest['id']}/archive",
            headers=headers,
            json=archive_payload,
        )

    assert restored.status_code == 200
    assert legacy_replay.status_code == 200
    assert legacy_replay.json() == restored.json()
    assert parent_archived.status_code == 200
    assert legacy_replay_after_parent.status_code == 404
    with auth_session_factory() as session:
        assert session.scalar(
            select(func.count())
            .select_from(ProgressEvent)
            .where(ProgressEvent.event_type == "quest_archived")
        ) == 1
        assert session.scalar(
            select(func.count())
            .select_from(ProgressEvent)
            .where(ProgressEvent.event_type == "quest_restored")
        ) == 1


def test_quest_archive_enforces_owner_version_and_campaign_boundary(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        first = register(client)
        second = register(
            client,
            email="quest-archive@example.com",
            installation={
                **dict(registration_payload()["installation"]),
                "installation_id": "d0000000-0000-4000-8000-000000000008",
            },
        )
        campaign, quest = _create_campaign_and_quest(client, bearer(second["access_token"]))
        edited = client.patch(
            f"/api/v1/quests/{quest['id']}",
            headers=bearer(second["access_token"]),
            json={
                "title": "Newer",
                "record_version": 1,
                "client_mutation_id": "d0000000-0000-4000-8000-000000000009",
            },
        )
        stale = client.post(
            f"/api/v1/quests/{quest['id']}/archive",
            headers=bearer(second["access_token"]),
            json={
                "record_version": 1,
                "client_mutation_id": "d0000000-0000-4000-8000-00000000000a",
            },
        )
        cross_user = client.post(
            f"/api/v1/quests/{quest['id']}/archive",
            headers=bearer(first["access_token"]),
            json={
                "record_version": edited.json()["record_version"],
                "client_mutation_id": "d0000000-0000-4000-8000-00000000000b",
            },
        )
        client.post(
            f"/api/v1/campaigns/{campaign['id']}/archive",
            headers=bearer(second["access_token"]),
            json={
                "record_version": edited.json()["campaign_record_version"],
                "client_mutation_id": "d0000000-0000-4000-8000-00000000000c",
            },
        )
        blocked = client.post(
            f"/api/v1/quests/{quest['id']}/archive",
            headers=bearer(second["access_token"]),
            json={
                "record_version": edited.json()["record_version"],
                "client_mutation_id": "d0000000-0000-4000-8000-00000000000d",
            },
        )

    assert stale.status_code == 409
    assert stale.json()["current"]["title"] == "Newer"
    assert cross_user.status_code == 404
    assert blocked.status_code == 404
    with auth_session_factory() as session:
        stored = session.get(Quest, UUID(quest["id"]))
        assert stored is not None and stored.definition_state == "active"
