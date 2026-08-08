from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import Campaign, Quest
from tests.campaigns.helpers import bearer, create_auth_client, register


def test_quest_assignment_is_stable_and_campaign_reads_are_exact(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        first_campaign = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={
                "title": "First",
                "client_mutation_id": "e0000000-0000-4000-8000-000000000001",
            },
        ).json()
        second_campaign = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={
                "title": "Second",
                "client_mutation_id": "e0000000-0000-4000-8000-000000000002",
            },
        ).json()
        quest = client.post(
            f"/api/v1/campaigns/{first_campaign['id']}/quests",
            headers=headers,
            json={
                "title": "Fixed assignment",
                "difficulty": "medium",
                "campaign_record_version": 1,
                "client_mutation_id": "e0000000-0000-4000-8000-000000000003",
            },
        ).json()
        first_detail = client.get(
            f"/api/v1/campaigns/{first_campaign['id']}", headers=headers
        )
        second_detail = client.get(
            f"/api/v1/campaigns/{second_campaign['id']}", headers=headers
        )
        move = client.patch(
            f"/api/v1/quests/{quest['id']}",
            headers=headers,
            json={
                "campaign_id": second_campaign["id"],
                "record_version": 1,
                "client_mutation_id": "e0000000-0000-4000-8000-000000000004",
            },
        )

    assert quest["campaign_id"] == first_campaign["id"]
    assert [item["id"] for item in first_detail.json()["quests"]] == [quest["id"]]
    assert second_detail.json()["quests"] == []
    assert move.status_code == 422
    with auth_session_factory() as session:
        stored = session.get(Quest, UUID(quest["id"]))
        assert stored is not None
        assert stored.campaign_id == UUID(first_campaign["id"])


def test_database_rejects_cross_owner_campaign_assignment(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        first = register(client)
        second = register(
            client,
            email="assignment-owner@example.com",
            installation={
                "installation_id": "e0000000-0000-4000-8000-000000000005",
                "platform": "android",
                "app_environment": "development",
            },
        )
        campaign = client.post(
            "/api/v1/campaigns",
            headers=bearer(second["access_token"]),
            json={
                "title": "Other owner",
                "client_mutation_id": "e0000000-0000-4000-8000-000000000006",
            },
        ).json()

    with auth_session_factory() as session:
        foreign_campaign = session.get(Campaign, UUID(campaign["id"]))
        assert foreign_campaign is not None
        session.add(
            Quest(
                user_id=UUID(str(first["user"]["id"])),
                campaign_id=foreign_campaign.id,
                quest_type="one_time",
                title="Invalid owner",
            )
        )
        with pytest.raises(IntegrityError):
            session.flush()
        session.rollback()
