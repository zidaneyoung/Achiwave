from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import (
    ProgressEvent,
    QuestCompletion,
    QuestCompletionReversal,
    XpLedgerEntry,
)
from tests.auth.test_registration import PASSWORD, registration_payload
from tests.completions.helpers import (
    bearer,
    create_auth_client,
    create_campaign_and_quest,
    register,
)
from tests.history.test_archival_integrity import _seed_populated_history


def test_owner_history_survives_replay_reversal_archive_restore_logout_and_recompletion(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        owner = register(client)
        headers = bearer(owner["access_token"])
        _, quest = create_campaign_and_quest(client, headers)
        occurrence_id = quest["occurrence"]["id"]
        history_path = f"/api/v1/quest-occurrences/{occurrence_id}/completion-history"
        completion_payload = {
            "client_mutation_id": "d6000000-0000-4000-8000-000000000001",
            "expected_occurrence_version": 1,
        }
        completed = client.post(
            f"/api/v1/quest-occurrences/{occurrence_id}/complete",
            headers=headers,
            json=completion_payload,
        )
        replay = client.post(
            f"/api/v1/quest-occurrences/{occurrence_id}/complete",
            headers=headers,
            json=completion_payload,
        )
        assert completed.status_code == 200
        assert replay.status_code == 200
        assert replay.json() == completed.json()

        first_completion = completed.json()["completion"]
        reversed_response = client.post(
            f"/api/v1/quest-completions/{first_completion['id']}/reverse",
            headers=headers,
            json={
                "client_mutation_id": "d6000000-0000-4000-8000-000000000002",
                "expected_occurrence_version": 2,
                "reason": "user_correction",
            },
        )
        assert reversed_response.status_code == 200

        archived = client.post(
            f"/api/v1/quests/{quest['id']}/archive",
            headers=headers,
            json={
                "client_mutation_id": "d6000000-0000-4000-8000-000000000003",
                "record_version": quest["record_version"],
            },
        )
        assert archived.status_code == 200
        restored = client.post(
            f"/api/v1/quests/{quest['id']}/restore",
            headers=headers,
            json={
                "client_mutation_id": "d6000000-0000-4000-8000-000000000004",
                "record_version": archived.json()["record_version"],
            },
        )
        assert restored.status_code == 200

        recompleted = client.post(
            f"/api/v1/quest-occurrences/{occurrence_id}/complete",
            headers=headers,
            json={
                "client_mutation_id": "d6000000-0000-4000-8000-000000000005",
                "expected_occurrence_version": 3,
            },
        )
        assert recompleted.status_code == 200
        assert recompleted.json()["completion"]["id"] != first_completion["id"]

        current = client.get(f"/api/v1/quests/{quest['id']}", headers=headers)
        history = client.get(history_path, headers=headers)
        assert current.status_code == 200
        assert current.json()["occurrence"]["active_completion_id"] == (
            recompleted.json()["completion"]["id"]
        )
        assert "items" not in current.json()["occurrence"]
        assert history.status_code == 200
        assert history.json()["occurrence_id"] == occurrence_id
        assert history.json()["total"] == 2
        assert history.json()["limit"] == 50
        assert history.json()["offset"] == 0
        assert len(history.json()["items"]) == 2
        assert history.json()["items"][0]["completion"]["id"] == first_completion["id"]
        assert history.json()["items"][0]["reversal"]["id"] == (
            reversed_response.json()["reversal"]["id"]
        )
        assert history.json()["items"][1]["reversal"] is None
        second_page = client.get(
            f"{history_path}?limit=1&offset=1", headers=headers
        )
        assert second_page.status_code == 200
        assert second_page.json()["total"] == 2
        assert second_page.json()["limit"] == 1
        assert second_page.json()["offset"] == 1
        assert [item["completion"]["id"] for item in second_page.json()["items"]] == [
            recompleted.json()["completion"]["id"]
        ]
        event_sequences = [
            event["event_sequence"]
            for item in history.json()["items"]
            for event in item["progress_events"]
        ]
        assert event_sequences == sorted(event_sequences)

        logged_out = client.post(
            "/api/v1/auth/logout",
            headers=headers,
            json={"refresh_token": owner["refresh_token"]},
        )
        assert logged_out.status_code == 204
        assert client.get(history_path, headers=headers).status_code == 401
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "Person@example.com",
                "password": PASSWORD,
                "installation": registration_payload()["installation"],
            },
        )
        assert login.status_code == 200
        relogged_history = client.get(
            history_path,
            headers=bearer(login.json()["access_token"]),
        )
        assert relogged_history.status_code == 200
        assert relogged_history.json() == history.json()

        other = register(
            client,
            email="completion-history-other@example.com",
            installation={
                **dict(registration_payload()["installation"]),
                "installation_id": "d6000000-0000-4000-8000-000000000006",
            },
        )
        cross_user = client.get(history_path, headers=bearer(other["access_token"]))
        assert cross_user.status_code == 404

    with auth_session_factory() as session:
        assert session.scalar(select(func.count()).select_from(QuestCompletion)) == 2
        assert session.scalar(
            select(func.count()).select_from(QuestCompletionReversal)
        ) == 1
        assert session.scalar(select(func.count()).select_from(XpLedgerEntry)) == 0
        assert session.scalars(
            select(ProgressEvent.event_sequence)
            .where(ProgressEvent.user_id == UUID(str(owner["user"]["id"])))
            .order_by(ProgressEvent.event_sequence)
        ).all() == list(range(1, 9))


def test_owner_can_query_legacy_history_without_device_or_mutation_context(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        owner = register(client)
        graph = _seed_populated_history(
            auth_session_factory,
            UUID(str(owner["user"]["id"])),
        )
        response = client.get(
            "/api/v1/quest-occurrences/"
            f"{graph.historical_occurrence_id}/completion-history",
            headers=bearer(owner["access_token"]),
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    item = response.json()["items"][0]
    assert item["completion"]["device_id"] is None
    assert item["completion"]["client_mutation_id"] is None
    assert item["reversal"]["device_id"] is None
    assert item["reversal"]["client_mutation_id"] is None
    assert item["reversal"]["reason"] == "Correct historical completion"
