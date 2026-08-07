from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import (
    Campaign,
    ClientMutation,
    Quest,
    QuestCompletion,
    QuestOccurrence,
    XpLedgerEntry,
)
from tests.campaigns.helpers import bearer, create_auth_client, register, registration_payload


def test_one_time_quest_creation_is_atomic_authoritative_and_replay_safe(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={
                "title": "Launch",
                "client_mutation_id": "b0000000-0000-4000-8000-000000000001",
            },
        ).json()
        payload = {
            "title": "  Write brief  ",
            "reward_xp": 20,
            "campaign_record_version": campaign["record_version"],
            "client_mutation_id": "b0000000-0000-4000-8000-000000000002",
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
    assert result["title"] == "Write brief"
    assert result["quest_type"] == "one_time"
    assert result["definition_state"] == "active"
    assert result["reward_xp"] == 20
    assert result["record_version"] == 1
    assert result["campaign_record_version"] == 2
    assert result["occurrence"]["status"] == "available"
    assert result["occurrence"]["reward_xp"] == 20
    assert result["occurrence"]["timezone_name"] == registration["timezone_name"]
    with auth_session_factory() as session:
        quest_id = UUID(result["id"])
        assert session.scalar(
            select(func.count()).select_from(Quest).where(Quest.id == quest_id)
        ) == 1
        assert session.scalar(
            select(func.count())
            .select_from(QuestOccurrence)
            .where(QuestOccurrence.quest_id == quest_id)
        ) == 1
        assert session.scalar(
            select(func.count())
            .select_from(ClientMutation)
            .where(ClientMutation.operation_type == "one_time_quest_create")
        ) == 1
        assert session.scalar(select(func.count()).select_from(QuestCompletion)) == 0
        assert session.scalar(select(func.count()).select_from(XpLedgerEntry)) == 0


def test_one_time_quest_creation_serializes_exact_concurrent_replay(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={
                "title": "Concurrent",
                "client_mutation_id": "b0000000-0000-4000-8000-000000000003",
            },
        ).json()
    payload = {
        "title": "One logical quest",
        "reward_xp": 0,
        "campaign_record_version": 1,
        "client_mutation_id": "b0000000-0000-4000-8000-000000000004",
    }

    def submit() -> tuple[int, dict[str, object]]:
        with create_auth_client(auth_database_url, auth_session_factory) as client:
            response = client.post(
                f"/api/v1/campaigns/{campaign['id']}/quests",
                headers=headers,
                json=payload,
            )
            return response.status_code, response.json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: submit(), range(2)))

    assert [status for status, _ in results] == [201, 201]
    assert results[0][1] == results[1][1]
    with auth_session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Quest)) == 1
        assert session.scalar(select(func.count()).select_from(QuestOccurrence)) == 1


def test_one_time_quest_creation_enforces_campaign_owner_state_version_and_shape(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        first = register(client)
        second = register(
            client,
            email="quest-owner@example.com",
            installation={
                **dict(registration_payload()["installation"]),
                "installation_id": "b0000000-0000-4000-8000-000000000005",
            },
        )
        campaign = client.post(
            "/api/v1/campaigns",
            headers=bearer(second["access_token"]),
            json={
                "title": "Private",
                "client_mutation_id": "b0000000-0000-4000-8000-000000000006",
            },
        ).json()
        common = {
            "title": "Private quest",
            "campaign_record_version": 1,
            "client_mutation_id": "b0000000-0000-4000-8000-000000000007",
        }
        cross_user = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=bearer(first["access_token"]),
            json=common,
        )
        edited = client.patch(
            f"/api/v1/campaigns/{campaign['id']}",
            headers=bearer(second["access_token"]),
            json={
                "title": "Private updated",
                "record_version": 1,
                "client_mutation_id": "b0000000-0000-4000-8000-000000000009",
            },
        )
        stale = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=bearer(second["access_token"]),
            json=common,
        )
        archived = client.post(
            f"/api/v1/campaigns/{campaign['id']}/archive",
            headers=bearer(second["access_token"]),
            json={
                "record_version": edited.json()["record_version"],
                "client_mutation_id": "b0000000-0000-4000-8000-000000000008",
            },
        )
        blocked = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=bearer(second["access_token"]),
            json={**common, "campaign_record_version": archived.json()["record_version"]},
        )
        untrusted = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=bearer(second["access_token"]),
            json={**common, "quest_type": "recurring", "owner_id": second["user"]["id"]},
        )

    assert cross_user.status_code == 404
    assert stale.status_code == 409
    assert stale.json()["current"]["record_version"] == 2
    assert blocked.status_code == 404
    assert untrusted.status_code == 422
    with auth_session_factory() as session:
        stored = session.get(Campaign, UUID(campaign["id"]))
        assert stored is not None and stored.campaign_state == "archived"
        assert session.scalar(select(func.count()).select_from(Quest)) == 0
