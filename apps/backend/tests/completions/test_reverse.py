from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import (
    ProgressEvent,
    QuestCompletion,
    QuestCompletionReversal,
    QuestOccurrence,
    XpLedgerEntry,
)
from tests.completions.helpers import (
    bearer,
    create_auth_client,
    create_campaign_and_quest,
    register,
)


def _complete(client, headers, occurrence: dict[str, object]) -> dict[str, object]:
    response = client.post(
        f"/api/v1/quest-occurrences/{occurrence['id']}/complete",
        headers=headers,
        json={
            "client_mutation_id": "d1000000-0000-4000-8000-000000000001",
            "expected_occurrence_version": occurrence["record_version"],
        },
    )
    assert response.status_code == 200
    return response.json()


def test_owner_reverses_after_archive_without_erasing_history(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        _, quest = create_campaign_and_quest(client, headers)
        completed = _complete(client, headers, quest["occurrence"])
        archived = client.post(
            f"/api/v1/campaigns/{quest['campaign_id']}/archive",
            headers=headers,
            json={
                "record_version": completed["campaign"]["record_version"],
                "client_mutation_id": "d1000000-0000-4000-8000-000000000002",
            },
        )
        assert archived.status_code == 200
        payload = {
            "client_mutation_id": "d1000000-0000-4000-8000-000000000003",
            "expected_occurrence_version": completed["occurrence"]["record_version"],
            "reason": "user_correction",
        }
        reversed_response = client.post(
            f"/api/v1/quest-completions/{completed['completion']['id']}/reverse",
            headers=headers,
            json=payload,
        )
        replay = client.post(
            f"/api/v1/quest-completions/{completed['completion']['id']}/reverse",
            headers=headers,
            json=payload,
        )

    assert reversed_response.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == reversed_response.json()
    result = reversed_response.json()
    assert result["outcome"] == "reversed"
    assert result["occurrence"]["status"] == "reversed"
    assert result["occurrence"]["record_version"] == 3
    assert result["completion"]["id"] == completed["completion"]["id"]
    assert result["completion"]["reversed_at"] is not None
    assert result["reversal"]["reason"] == "user_correction"
    assert result["reversal"]["event_sequence"] == 4
    assert result["campaign"]["status"] == "archived"

    with auth_session_factory() as session:
        completion_id = UUID(completed["completion"]["id"])
        occurrence_id = UUID(completed["occurrence"]["id"])
        assert session.scalar(
            select(func.count())
            .select_from(QuestCompletion)
            .where(QuestCompletion.id == completion_id)
        ) == 1
        assert session.scalar(
            select(func.count())
            .select_from(QuestCompletionReversal)
            .where(QuestCompletionReversal.completion_id == completion_id)
        ) == 1
        occurrence = session.get(QuestOccurrence, occurrence_id)
        assert occurrence is not None and occurrence.completed_at is not None
        assert occurrence.reversed_at is not None
        assert session.scalar(select(func.count()).select_from(ProgressEvent)) == 4
        assert session.scalar(select(func.count()).select_from(XpLedgerEntry)) == 0


def test_second_logical_reversal_returns_canonical_already_reversed(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        _, quest = create_campaign_and_quest(client, headers)
        completed = _complete(client, headers, quest["occurrence"])
        first = client.post(
            f"/api/v1/quest-completions/{completed['completion']['id']}/reverse",
            headers=headers,
            json={
                "client_mutation_id": "d1000000-0000-4000-8000-000000000004",
                "expected_occurrence_version": 2,
                "reason": "user_correction",
            },
        )
        second = client.post(
            f"/api/v1/quest-completions/{completed['completion']['id']}/reverse",
            headers=headers,
            json={
                "client_mutation_id": "d1000000-0000-4000-8000-000000000005",
                "expected_occurrence_version": 2,
                "reason": "user_correction",
            },
        )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["outcome"] == "already_reversed"
    assert second.json()["reversal"]["id"] == first.json()["reversal"]["id"]


def test_reversal_is_owner_scoped_and_rejects_unknown_fields(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        owner = register(client)
        owner_headers = bearer(owner["access_token"])
        _, quest = create_campaign_and_quest(client, owner_headers)
        completed = _complete(client, owner_headers, quest["occurrence"])
        other = register(
            client,
            email="reverse-other@example.com",
            installation={
                "installation_id": "d1000000-0000-4000-8000-000000000006",
                "platform": "android",
                "app_environment": "development",
                "app_version": "1.0.0",
                "build_version": "1",
            },
        )
        cross_user = client.post(
            f"/api/v1/quest-completions/{completed['completion']['id']}/reverse",
            headers=bearer(other["access_token"]),
            json={
                "client_mutation_id": "d1000000-0000-4000-8000-000000000007",
                "expected_occurrence_version": 2,
            },
        )
        malformed = client.post(
            f"/api/v1/quest-completions/{completed['completion']['id']}/reverse",
            headers=owner_headers,
            json={
                "client_mutation_id": "d1000000-0000-4000-8000-000000000008",
                "expected_occurrence_version": 2,
                "reason": "erase_history",
            },
        )

    assert cross_user.status_code == 404
    assert cross_user.json()["code"] == "completion_not_found"
    assert malformed.status_code == 422
