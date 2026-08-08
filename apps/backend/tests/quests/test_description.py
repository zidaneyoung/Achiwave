from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import Quest
from tests.campaigns.helpers import bearer, create_auth_client, register


def test_quest_description_create_edit_and_clear_use_existing_storage(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    assert "description" in Quest.__table__.columns
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={
                "title": "Descriptions",
                "client_mutation_id": "f0000000-0000-4000-8000-000000000001",
            },
        ).json()
        created = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=headers,
            json={
                "title": "Document",
                "difficulty": "medium",
                "description": "  First line\nSecond line  ",
                "campaign_record_version": 1,
                "client_mutation_id": "f0000000-0000-4000-8000-000000000002",
            },
        )
        updated = client.patch(
            f"/api/v1/quests/{created.json()['id']}",
            headers=headers,
            json={
                "description": "  Updated context  ",
                "record_version": 1,
                "client_mutation_id": "f0000000-0000-4000-8000-000000000003",
            },
        )
        cleared = client.patch(
            f"/api/v1/quests/{created.json()['id']}",
            headers=headers,
            json={
                "description": None,
                "record_version": 2,
                "client_mutation_id": "f0000000-0000-4000-8000-000000000004",
            },
        )

    assert created.status_code == 201
    assert created.json()["description"] == "First line\nSecond line"
    assert updated.status_code == 200
    assert updated.json()["description"] == "Updated context"
    assert cleared.status_code == 200
    assert cleared.json()["description"] is None
    with auth_session_factory() as session:
        stored = session.get(Quest, UUID(created.json()["id"]))
        assert stored is not None and stored.description is None


def test_quest_description_rejects_blank_unsafe_and_oversized_values(
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
                "title": "Validation",
                "client_mutation_id": "f0000000-0000-4000-8000-000000000005",
            },
        ).json()
        responses = [
            client.post(
                f"/api/v1/campaigns/{campaign['id']}/quests",
                headers=headers,
                json={
                    "title": "Invalid",
                    "difficulty": "medium",
                    "description": value,
                    "campaign_record_version": 1,
                    "client_mutation_id": mutation_id,
                },
            )
            for value, mutation_id in (
                ("   ", "f0000000-0000-4000-8000-000000000006"),
                ("unsafe\u0000", "f0000000-0000-4000-8000-000000000007"),
                ("x" * 4_001, "f0000000-0000-4000-8000-000000000008"),
            )
        ]

    assert [response.status_code for response in responses] == [422, 422, 422]
