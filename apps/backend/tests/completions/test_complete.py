from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import (
    Campaign,
    ClientMutation,
    ProgressEvent,
    QuestCompletion,
    QuestOccurrence,
    XpLedgerEntry,
)
from tests.completions.helpers import (
    bearer,
    create_auth_client,
    create_campaign_and_quest,
    register,
)


def test_owner_completes_available_occurrence_with_canonical_state(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        _, quest = create_campaign_and_quest(client, headers)
        occurrence = quest["occurrence"]
        response = client.post(
            f"/api/v1/quest-occurrences/{occurrence['id']}/complete",
            headers=headers,
            json={
                "client_mutation_id": "d0000000-0000-4000-8000-000000000003",
                "expected_occurrence_version": occurrence["record_version"],
            },
        )
        detail = client.get(f"/api/v1/quests/{quest['id']}", headers=headers)

    assert response.status_code == 200
    result = response.json()
    assert result["outcome"] == "completed"
    assert result["occurrence"]["id"] == occurrence["id"]
    assert result["occurrence"]["status"] == "completed"
    assert result["occurrence"]["record_version"] == 2
    assert result["completion"]["occurrence_id"] == occurrence["id"]
    assert result["completion"]["event_sequence"] == 1
    assert result["campaign"]["status"] == "completed"
    assert [event["event_type"] for event in result["progress_events"]] == [
        "completion_accepted",
        "campaign_completed",
    ]
    assert detail.status_code == 200
    assert detail.json()["occurrence"]["active_completion_id"] == result["completion"]["id"]

    with auth_session_factory() as session:
        occurrence_id = UUID(occurrence["id"])
        assert session.scalar(
            select(func.count())
            .select_from(QuestCompletion)
            .where(QuestCompletion.occurrence_id == occurrence_id)
        ) == 1
        assert session.scalar(
            select(func.count())
            .select_from(ClientMutation)
            .where(ClientMutation.operation_type == "quest_occurrence_complete")
        ) == 1
        assert session.scalar(select(func.count()).select_from(ProgressEvent)) == 2
        assert session.scalar(select(func.count()).select_from(XpLedgerEntry)) == 0
        canonical_occurrence = session.get(QuestOccurrence, occurrence_id)
        assert canonical_occurrence is not None
        assert canonical_occurrence.completed_at is not None
        campaign = session.get(Campaign, UUID(result["campaign"]["id"]))
        assert campaign is not None and campaign.campaign_state == "completed"


def test_completion_rejects_stale_archived_and_cross_user_targets(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        owner = register(client)
        owner_headers = bearer(owner["access_token"])
        campaign, quest = create_campaign_and_quest(client, owner_headers)
        occurrence = quest["occurrence"]
        other = register(
            client,
            email="completion-other@example.com",
            installation={
                "installation_id": "d0000000-0000-4000-8000-000000000004",
                "platform": "android",
                "app_environment": "development",
                "app_version": "1.0.0",
                "build_version": "1",
            },
        )

        cross_user = client.post(
            f"/api/v1/quest-occurrences/{occurrence['id']}/complete",
            headers=bearer(other["access_token"]),
            json={
                "client_mutation_id": "d0000000-0000-4000-8000-000000000005",
                "expected_occurrence_version": 1,
            },
        )
        stale = client.post(
            f"/api/v1/quest-occurrences/{occurrence['id']}/complete",
            headers=owner_headers,
            json={
                "client_mutation_id": "d0000000-0000-4000-8000-000000000006",
                "expected_occurrence_version": 99,
            },
        )
        archived = client.post(
            f"/api/v1/campaigns/{campaign['id']}/archive",
            headers=owner_headers,
            json={
                "record_version": quest["campaign_record_version"],
                "client_mutation_id": "d0000000-0000-4000-8000-000000000007",
            },
        )
        assert archived.status_code == 200
        ineligible = client.post(
            f"/api/v1/quest-occurrences/{occurrence['id']}/complete",
            headers=owner_headers,
            json={
                "client_mutation_id": "d0000000-0000-4000-8000-000000000008",
                "expected_occurrence_version": 1,
            },
        )

    assert cross_user.status_code == 404
    assert cross_user.json()["code"] == "occurrence_not_found"
    assert stale.status_code == 409
    assert stale.json()["code"] == "stale_occurrence_version"
    assert stale.json()["current"]["occurrence"]["record_version"] == 1
    assert ineligible.status_code == 409
    assert ineligible.json()["code"] == "occurrence_not_eligible"


def test_completion_rejects_unknown_fields_and_requires_authentication(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        unauthenticated = client.post(
            "/api/v1/quest-occurrences/d0000000-0000-4000-8000-000000000009/complete",
            json={
                "client_mutation_id": "d0000000-0000-4000-8000-000000000010",
                "expected_occurrence_version": 1,
            },
        )
        registration = register(client)
        _, quest = create_campaign_and_quest(client, bearer(registration["access_token"]))
        unknown = client.post(
            f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete",
            headers=bearer(registration["access_token"]),
            json={
                "client_mutation_id": "d0000000-0000-4000-8000-000000000011",
                "expected_occurrence_version": 1,
                "user_id": registration["user"]["id"],
            },
        )

    assert unauthenticated.status_code == 401
    assert unknown.status_code == 422
    assert unknown.json()["code"] == "validation_error"
