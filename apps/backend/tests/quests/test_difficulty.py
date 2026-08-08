from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import Quest, QuestOccurrence, XpLedgerEntry
from tests.campaigns.helpers import bearer, create_auth_client, register


def _campaign(client, headers: dict[str, str]) -> dict[str, object]:
    response = client.post(
        "/api/v1/campaigns",
        headers=headers,
        json={
            "title": "Difficulty",
            "client_mutation_id": "ed000000-0000-4000-8000-000000000001",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_difficulty_is_required_canonical_and_independent_from_reward(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = _campaign(client, headers)
        missing = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=headers,
            json={
                "title": "Missing",
                "campaign_record_version": 1,
                "client_mutation_id": "ed000000-0000-4000-8000-000000000002",
            },
        )
        invalid = [
            client.post(
                f"/api/v1/campaigns/{campaign['id']}/quests",
                headers=headers,
                json={
                    "title": "Invalid",
                    "difficulty": value,
                    "campaign_record_version": 1,
                    "client_mutation_id": mutation_id,
                },
            )
            for value, mutation_id in [
                ("Easy", "ed000000-0000-4000-8000-000000000003"),
                (" easy", "ed000000-0000-4000-8000-000000000004"),
                ("", "ed000000-0000-4000-8000-000000000005"),
                ("extreme", "ed000000-0000-4000-8000-000000000006"),
            ]
        ]
        easy_high_reward = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=headers,
            json={
                "title": "Independent",
                "difficulty": "easy",
                "reward_xp": 20,
                "campaign_record_version": 1,
                "client_mutation_id": "ed000000-0000-4000-8000-000000000007",
            },
        )

    assert missing.status_code == 422
    assert [response.status_code for response in invalid] == [422, 422, 422, 422]
    assert easy_high_reward.status_code == 201
    assert easy_high_reward.json()["difficulty"] == "easy"
    assert easy_high_reward.json()["difficulty_label"] == "Easy"
    assert easy_high_reward.json()["reward_xp"] == 20
    with auth_session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Quest)) == 1
        assert session.scalar(select(func.count()).select_from(XpLedgerEntry)) == 0


def test_legacy_null_difficulty_remains_readable_until_explicitly_edited(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = _campaign(client, headers)
        created = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=headers,
            json={
                "title": "Legacy",
                "difficulty": "medium",
                "reward_xp": 10,
                "campaign_record_version": 1,
                "client_mutation_id": "ed000000-0000-4000-8000-000000000010",
            },
        ).json()
        with auth_session_factory.begin() as session:
            quest = session.get(Quest, UUID(created["id"]))
            assert quest is not None
            quest.difficulty = None
        detail = client.get(f"/api/v1/quests/{created['id']}", headers=headers)
        unrelated = client.patch(
            f"/api/v1/quests/{created['id']}",
            headers=headers,
            json={
                "title": "Legacy renamed",
                "record_version": created["record_version"],
                "client_mutation_id": "ed000000-0000-4000-8000-000000000011",
            },
        )
        explicit_null = client.patch(
            f"/api/v1/quests/{created['id']}",
            headers=headers,
            json={
                "difficulty": None,
                "record_version": unrelated.json()["record_version"],
                "client_mutation_id": "ed000000-0000-4000-8000-000000000012",
            },
        )
        configured = client.patch(
            f"/api/v1/quests/{created['id']}",
            headers=headers,
            json={
                "difficulty": "hard",
                "record_version": unrelated.json()["record_version"],
                "client_mutation_id": "ed000000-0000-4000-8000-000000000013",
            },
        )
        archived = client.post(
            f"/api/v1/quests/{created['id']}/archive",
            headers=headers,
            json={
                "record_version": configured.json()["record_version"],
                "client_mutation_id": "ed000000-0000-4000-8000-000000000014",
            },
        )
        restored = client.post(
            f"/api/v1/quests/{created['id']}/restore",
            headers=headers,
            json={
                "record_version": archived.json()["record_version"],
                "client_mutation_id": "ed000000-0000-4000-8000-000000000015",
            },
        )

    assert detail.status_code == 200
    assert detail.json()["difficulty"] is None
    assert detail.json()["difficulty_label"] == "Not set"
    assert unrelated.status_code == 200
    assert unrelated.json()["difficulty"] is None
    assert explicit_null.status_code == 422
    assert configured.status_code == 200
    assert configured.json()["difficulty"] == "hard"
    assert configured.json()["occurrence"] == created["occurrence"]
    assert archived.json()["difficulty"] == "hard"
    assert restored.json()["difficulty"] == "hard"
    with auth_session_factory() as session:
        occurrence = session.scalar(
            select(QuestOccurrence).where(
                QuestOccurrence.quest_id == UUID(created["id"])
            )
        )
        assert occurrence is not None and occurrence.reward_xp == 10
