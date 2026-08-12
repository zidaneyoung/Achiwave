from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import (
    ClientMutation,
    ProgressEvent,
    QuestCompletion,
    QuestOccurrence,
    RegisteredDevice,
    User,
    XpLedgerEntry,
)
from achiwave_backend.schemas.completions import CompleteOccurrenceRequest
from achiwave_backend.services.completions import CompletionService
from tests.completions.helpers import (
    bearer,
    create_auth_client,
    create_campaign_and_quest,
    register,
)


def test_exact_concurrent_replay_returns_one_original_result(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        _, quest = create_campaign_and_quest(client, headers)
    path = f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete"
    payload = {
        "client_mutation_id": "d5000000-0000-4000-8000-000000000001",
        "expected_occurrence_version": 1,
    }
    barrier = Barrier(2)

    def submit() -> tuple[int, dict[str, object]]:
        with create_auth_client(auth_database_url, auth_session_factory) as client:
            barrier.wait()
            response = client.post(path, headers=headers, json=payload)
            return response.status_code, response.json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: submit(), range(2)))

    assert [result[0] for result in results] == [200, 200]
    assert results[0][1] == results[1][1]
    assert results[0][1]["outcome"] == "completed"
    with auth_session_factory() as session:
        assert session.scalar(select(func.count()).select_from(QuestCompletion)) == 1
        assert session.scalar(
            select(func.count())
            .select_from(ClientMutation)
            .where(ClientMutation.operation_type == "quest_occurrence_complete")
        ) == 1
        assert session.scalar(select(func.count()).select_from(ProgressEvent)) == 2
        assert session.scalar(select(func.count()).select_from(XpLedgerEntry)) == 0


def test_different_mutations_racing_one_occurrence_converge_without_side_effects(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        _, quest = create_campaign_and_quest(client, headers)
    path = f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete"
    barrier = Barrier(2)

    def submit(mutation_suffix: int) -> tuple[int, dict[str, object]]:
        with create_auth_client(auth_database_url, auth_session_factory) as client:
            barrier.wait()
            response = client.post(
                path,
                headers=headers,
                json={
                    "client_mutation_id": (
                        f"d5000000-0000-4000-8000-{mutation_suffix:012d}"
                    ),
                    "expected_occurrence_version": 1,
                },
            )
            return response.status_code, response.json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(submit, (2, 3)))

    assert [result[0] for result in results] == [200, 200]
    assert {result[1]["outcome"] for result in results} == {
        "completed",
        "duplicate_completion",
    }
    assert len({result[1]["completion"]["id"] for result in results}) == 1
    assert len(
        {result[1]["completion"]["server_received_at"] for result in results}
    ) == 1
    with auth_session_factory() as session:
        assert session.scalar(select(func.count()).select_from(QuestCompletion)) == 1
        assert session.scalar(
            select(func.count())
            .select_from(ClientMutation)
            .where(ClientMutation.operation_type == "quest_occurrence_complete")
        ) == 2
        assert session.scalar(select(func.count()).select_from(ProgressEvent)) == 2
        assert session.scalar(select(func.count()).select_from(XpLedgerEntry)) == 0


def test_stale_failure_is_bound_and_exactly_replayed(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    mutation_id = "d5000000-0000-4000-8000-000000000004"
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        _, quest = create_campaign_and_quest(client, headers)
        path = f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete"
        payload = {
            "client_mutation_id": mutation_id,
            "expected_occurrence_version": 99,
        }
        first = client.post(path, headers=headers, json=payload)
        replay = client.post(path, headers=headers, json=payload)
        mismatch = client.post(
            path,
            headers=headers,
            json={**payload, "expected_occurrence_version": 1},
        )

    assert first.status_code == 409
    assert replay.status_code == 409
    assert replay.json() == first.json()
    assert mismatch.status_code == 409
    assert mismatch.json()["code"] == "client_mutation_conflict"
    with auth_session_factory() as session:
        mutation = session.scalar(
            select(ClientMutation).where(
                ClientMutation.client_mutation_id == UUID(mutation_id)
            )
        )
        assert mutation is not None
        assert mutation.processing_status == "permanent_failure"
        assert mutation.safe_error_class == "stale_occurrence_version"
        assert mutation.result_payload == {
            "error": {
                "code": first.json()["code"],
                "message": first.json()["message"],
                "current": first.json()["current"],
            }
        }
        assert session.scalar(select(func.count()).select_from(QuestCompletion)) == 0
        assert session.scalar(select(func.count()).select_from(ProgressEvent)) == 0


def test_transaction_rollback_leaves_no_partial_effect_and_retry_can_succeed(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    mutation_id = UUID("d5000000-0000-4000-8000-000000000005")
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        _, quest = create_campaign_and_quest(client, headers)

    with auth_session_factory() as session:
        user = session.scalar(select(User))
        device = session.scalar(select(RegisteredDevice))
        assert user is not None and device is not None
        request = CompleteOccurrenceRequest(
            client_mutation_id=mutation_id,
            expected_occurrence_version=1,
        )
        with patch.object(session, "commit", side_effect=RuntimeError("interrupted")):
            with pytest.raises(RuntimeError, match="interrupted"):
                CompletionService().complete(
                    session,
                    user,
                    device,
                    UUID(quest["occurrence"]["id"]),
                    request,
                )

    with auth_session_factory() as session:
        occurrence = session.get(
            QuestOccurrence,
            UUID(quest["occurrence"]["id"]),
        )
        assert occurrence is not None
        assert occurrence.occurrence_state == "available"
        assert occurrence.record_version == 1
        assert session.scalar(select(func.count()).select_from(QuestCompletion)) == 0
        assert session.scalar(
            select(func.count())
            .select_from(ClientMutation)
            .where(ClientMutation.client_mutation_id == mutation_id)
        ) == 0
        assert session.scalar(select(func.count()).select_from(ProgressEvent)) == 0

    with create_auth_client(auth_database_url, auth_session_factory) as client:
        retry = client.post(
            f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete",
            headers=headers,
            json={
                "client_mutation_id": str(mutation_id),
                "expected_occurrence_version": 1,
            },
        )
    assert retry.status_code == 200
    assert retry.json()["outcome"] == "completed"
