from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import (
    ClientMutation,
    QuestCompletion,
    QuestCompletionReversal,
)
from tests.completions.helpers import (
    bearer,
    create_auth_client,
    create_campaign_and_quest,
    register,
)


def test_mutation_binding_includes_authenticated_device_and_canonical_payload(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    mutation_id = "d4000000-0000-4000-8000-000000000001"
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        _, quest = create_campaign_and_quest(client, headers)
        response = client.post(
            f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete",
            headers=headers,
            json={
                "client_mutation_id": mutation_id,
                "expected_occurrence_version": 1,
            },
        )

    assert response.status_code == 200
    result = response.json()
    assert result["completion"]["device_id"] == registration["device_id"]
    with auth_session_factory() as session:
        mutation = session.scalar(
            select(ClientMutation).where(
                ClientMutation.client_mutation_id == UUID(mutation_id)
            )
        )
        completion = session.get(
            QuestCompletion,
            UUID(result["completion"]["id"]),
        )
        assert mutation is not None
        assert mutation.device_id == UUID(registration["device_id"])
        assert mutation.operation_type == "quest_occurrence_complete"
        assert mutation.target_type == "quest_occurrence"
        assert mutation.target_id == UUID(quest["occurrence"]["id"])
        assert mutation.processing_status == "succeeded"
        assert len(mutation.payload_hash) == 32
        assert completion is not None
        assert mutation.result_id == completion.id
        assert completion.device_id == mutation.device_id


def test_mutation_identifier_cannot_be_reused_for_changed_payload_or_operation(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    mutation_id = "d4000000-0000-4000-8000-000000000002"
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        _, quest = create_campaign_and_quest(client, headers)
        completed = client.post(
            f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete",
            headers=headers,
            json={
                "client_mutation_id": mutation_id,
                "expected_occurrence_version": 1,
            },
        )
        changed_payload = client.post(
            f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete",
            headers=headers,
            json={
                "client_mutation_id": mutation_id,
                "expected_occurrence_version": 2,
            },
        )
        changed_operation = client.post(
            f"/api/v1/quest-completions/{completed.json()['completion']['id']}/reverse",
            headers=headers,
            json={
                "client_mutation_id": mutation_id,
                "expected_occurrence_version": 2,
                "reason": "user_correction",
            },
        )

    assert completed.status_code == 200
    assert changed_payload.status_code == 409
    assert changed_payload.json()["code"] == "client_mutation_conflict"
    assert changed_operation.status_code == 409
    assert changed_operation.json()["code"] == "client_mutation_conflict"
    with auth_session_factory() as session:
        assert session.scalar(
            select(func.count())
            .select_from(ClientMutation)
            .where(ClientMutation.client_mutation_id == UUID(mutation_id))
        ) == 1
        assert session.scalar(select(func.count()).select_from(QuestCompletion)) == 1
        assert session.scalar(
            select(func.count()).select_from(QuestCompletionReversal)
        ) == 0


def test_malformed_mutation_identifier_is_rejected_before_processing(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        _, quest = create_campaign_and_quest(client, headers)
        response = client.post(
            f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete",
            headers=headers,
            json={
                "client_mutation_id": "not-a-uuid",
                "expected_occurrence_version": 1,
            },
        )

    assert response.status_code == 422
    with auth_session_factory() as session:
        assert session.scalar(
            select(func.count())
            .select_from(ClientMutation)
            .where(ClientMutation.operation_type == "quest_occurrence_complete")
        ) == 0
