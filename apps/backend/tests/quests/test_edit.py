from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import Campaign, ClientMutation, Quest, QuestOccurrence
from tests.campaigns.helpers import bearer, create_auth_client, register, registration_payload


def _create_quest(client, headers: dict[str, str]) -> dict[str, object]:
    campaign = client.post(
        "/api/v1/campaigns",
        headers=headers,
        json={
            "title": "Authoring",
            "client_mutation_id": "c0000000-0000-4000-8000-000000000001",
        },
    ).json()
    response = client.post(
        f"/api/v1/campaigns/{campaign['id']}/quests",
        headers=headers,
        json={
            "title": "Original",
            "difficulty": "medium",
            "reward_xp": 10,
            "campaign_record_version": campaign["record_version"],
            "client_mutation_id": "c0000000-0000-4000-8000-000000000002",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_quest_detail_and_edit_preserve_occurrence_snapshot_and_replay(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        created = _create_quest(client, headers)
        detail = client.get(f"/api/v1/quests/{created['id']}", headers=headers)
        payload = {
            "title": "  Updated  ",
            "reward_xp": 25,
            "record_version": created["record_version"],
            "client_mutation_id": "c0000000-0000-4000-8000-000000000003",
        }
        updated = client.patch(
            f"/api/v1/quests/{created['id']}", headers=headers, json=payload
        )
        replay = client.patch(
            f"/api/v1/quests/{created['id']}", headers=headers, json=payload
        )

    assert detail.status_code == 200
    assert detail.json() == created
    assert updated.status_code == 200
    assert replay.json() == updated.json()
    result = updated.json()
    assert result["title"] == "Updated"
    assert result["reward_xp"] == 25
    assert result["record_version"] == 2
    assert result["occurrence"]["id"] == created["occurrence"]["id"]
    assert result["occurrence"]["reward_xp"] == 10
    assert result["occurrence"]["available_at"] == created["occurrence"]["available_at"]
    with auth_session_factory() as session:
        occurrence = session.scalar(
            select(QuestOccurrence).where(QuestOccurrence.quest_id == UUID(created["id"]))
        )
        assert occurrence is not None and occurrence.reward_xp == 10
        assert session.scalar(
            select(func.count())
            .select_from(ClientMutation)
            .where(ClientMutation.operation_type == "one_time_quest_update")
        ) == 1


def test_quest_edit_returns_stale_canonical_state_and_rejects_immutable_fields(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        created = _create_quest(client, headers)
        accepted = client.patch(
            f"/api/v1/quests/{created['id']}",
            headers=headers,
            json={
                "title": "Current",
                "record_version": 1,
                "client_mutation_id": "c0000000-0000-4000-8000-000000000004",
            },
        )
        stale = client.patch(
            f"/api/v1/quests/{created['id']}",
            headers=headers,
            json={
                "title": "Stale",
                "record_version": 1,
                "client_mutation_id": "c0000000-0000-4000-8000-000000000005",
            },
        )
        untrusted = client.patch(
            f"/api/v1/quests/{created['id']}",
            headers=headers,
            json={
                "campaign_id": created["campaign_id"],
                "quest_type": "recurring",
                "definition_state": "archived",
                "record_version": 2,
                "client_mutation_id": "c0000000-0000-4000-8000-000000000006",
            },
        )

    assert accepted.status_code == 200
    assert stale.status_code == 409
    assert stale.json()["current"]["title"] == "Current"
    assert stale.json()["current"]["record_version"] == 2
    assert untrusted.status_code == 422


def test_quest_detail_and_edit_hide_cross_user_identifier(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        first = register(client)
        second = register(
            client,
            email="quest-editor@example.com",
            installation={
                **dict(registration_payload()["installation"]),
                "installation_id": "c0000000-0000-4000-8000-000000000007",
            },
        )
        created = _create_quest(client, bearer(second["access_token"]))
        detail = client.get(
            f"/api/v1/quests/{created['id']}", headers=bearer(first["access_token"])
        )
        edit = client.patch(
            f"/api/v1/quests/{created['id']}",
            headers=bearer(first["access_token"]),
            json={
                "title": "Attack",
                "record_version": 1,
                "client_mutation_id": "c0000000-0000-4000-8000-000000000008",
            },
        )

    assert detail.status_code == 404
    assert edit.status_code == 404
    with auth_session_factory() as session:
        quest = session.get(Quest, UUID(created["id"]))
        assert quest is not None and quest.title == "Original"


def test_completed_campaign_allows_snapshot_safe_quest_content_edit(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        created = _create_quest(client, headers)
        with auth_session_factory.begin() as session:
            campaign = session.get(Campaign, UUID(created["campaign_id"]))
            occurrence = session.get(QuestOccurrence, UUID(created["occurrence"]["id"]))
            assert campaign is not None and occurrence is not None
            completed_at = datetime.now(UTC)
            campaign.campaign_state = "completed"
            campaign.completed_at = completed_at
            occurrence.occurrence_state = "completed"
            occurrence.completed_at = completed_at
        edited = client.patch(
            f"/api/v1/quests/{created['id']}",
            headers=headers,
            json={
                "description": "Post-completion notes",
                "record_version": 1,
                "client_mutation_id": "c0000000-0000-4000-8000-000000000009",
            },
        )

    assert edited.status_code == 200
    assert edited.json()["campaign_status"] == "completed"
    assert edited.json()["occurrence"]["status"] == "completed"
