from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import Quest, QuestOccurrence, XpLedgerEntry
from tests.campaigns.helpers import bearer, create_auth_client, register


def test_category_options_are_authenticated_and_canonical(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        unauthorized = client.get("/api/v1/quests/authoring-options")
        registration = register(client)
        response = client.get(
            "/api/v1/quests/authoring-options",
            headers=bearer(registration["access_token"]),
        )

    assert unauthorized.status_code == 401
    assert response.status_code == 200
    assert response.json() == {
        "categories": [
            {"value": "personal", "label": "Personal"},
            {"value": "health", "label": "Health"},
            {"value": "learning", "label": "Learning"},
            {"value": "work", "label": "Work"},
            {"value": "finance", "label": "Finance"},
        ],
        "difficulties": [
            {"value": "easy", "label": "Easy"},
            {"value": "medium", "label": "Medium"},
            {"value": "hard", "label": "Hard"},
        ],
    }


def test_category_is_optional_validated_and_preserved_across_lifecycle(
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
                "title": "Categorized",
                "client_mutation_id": "ec000000-0000-4000-8000-000000000001",
            },
        ).json()
        uncategorized = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=headers,
            json={
                "title": "Uncategorized",
                "difficulty": "medium",
                "campaign_record_version": campaign["record_version"],
                "client_mutation_id": "ec000000-0000-4000-8000-000000000002",
            },
        )
        categorized = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=headers,
            json={
                "title": "Budget",
                "category": "finance",
                "difficulty": "hard",
                "reward_xp": 20,
                "campaign_record_version": uncategorized.json()["campaign_record_version"],
                "client_mutation_id": "ec000000-0000-4000-8000-000000000003",
            },
        )
        updated = client.patch(
            f"/api/v1/quests/{categorized.json()['id']}",
            headers=headers,
            json={
                "category": "health",
                "record_version": categorized.json()["record_version"],
                "client_mutation_id": "ec000000-0000-4000-8000-000000000004",
            },
        )
        archived = client.post(
            f"/api/v1/quests/{categorized.json()['id']}/archive",
            headers=headers,
            json={
                "record_version": updated.json()["record_version"],
                "client_mutation_id": "ec000000-0000-4000-8000-000000000005",
            },
        )
        restored = client.post(
            f"/api/v1/quests/{categorized.json()['id']}/restore",
            headers=headers,
            json={
                "record_version": archived.json()["record_version"],
                "client_mutation_id": "ec000000-0000-4000-8000-000000000006",
            },
        )

    assert uncategorized.status_code == 201
    assert uncategorized.json()["category"] is None
    assert uncategorized.json()["category_label"] == "Uncategorized"
    assert categorized.status_code == 201
    assert categorized.json()["category"] == "finance"
    assert categorized.json()["category_label"] == "Finance"
    assert updated.status_code == 200
    assert updated.json()["category"] == "health"
    assert updated.json()["category_label"] == "Health"
    assert updated.json()["occurrence"] == categorized.json()["occurrence"]
    assert archived.json()["category"] == "health"
    assert restored.json()["category"] == "health"
    with auth_session_factory() as session:
        quest_id = UUID(categorized.json()["id"])
        quest = session.get(Quest, quest_id)
        occurrence = session.scalar(
            select(QuestOccurrence).where(QuestOccurrence.quest_id == quest_id)
        )
        assert quest is not None and quest.category == "health"
        assert occurrence is not None and occurrence.reward_xp == 20
        assert session.scalar(select(func.count()).select_from(XpLedgerEntry)) == 0


def test_category_rejects_noncanonical_values_without_writes(
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
                "title": "Strict",
                "client_mutation_id": "ec000000-0000-4000-8000-000000000010",
            },
        ).json()
        responses = [
            client.post(
                f"/api/v1/campaigns/{campaign['id']}/quests",
                headers=headers,
                json={
                    "title": "Invalid",
                    "difficulty": "medium",
                    "category": invalid,
                    "campaign_record_version": campaign["record_version"],
                    "client_mutation_id": mutation_id,
                },
            )
            for invalid, mutation_id in [
                ("Finance", "ec000000-0000-4000-8000-000000000011"),
                (" finance", "ec000000-0000-4000-8000-000000000012"),
                ("", "ec000000-0000-4000-8000-000000000013"),
                ("other", "ec000000-0000-4000-8000-000000000014"),
            ]
        ]

    assert [response.status_code for response in responses] == [422, 422, 422, 422]
    with auth_session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Quest)) == 0
