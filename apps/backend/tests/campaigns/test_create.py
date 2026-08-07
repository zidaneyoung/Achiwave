from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import Campaign, ClientMutation, Quest
from tests.campaigns.helpers import bearer, create_auth_client, register

MUTATION_ID = "40000000-0000-4000-8000-000000000001"


def test_create_campaign_is_owner_scoped_atomic_and_exactly_replayable(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        payload = {
            "title": "  Ship Stage 6  ",
            "description": "  Campaign planning notes.  ",
            "client_mutation_id": MUTATION_ID,
        }
        created = client.post("/api/v1/campaigns", headers=headers, json=payload)
        replay = client.post("/api/v1/campaigns", headers=headers, json=payload)

    assert created.status_code == 201
    assert replay.status_code == 201
    assert replay.json() == created.json()
    result = created.json()
    UUID(result["id"])
    assert result["title"] == "Ship Stage 6"
    assert result["description"] == "Campaign planning notes."
    assert result["display_order"] == 0
    assert result["status"] == "active"
    assert result["record_version"] == 1
    assert result["completed_at"] is None
    assert result["archived_at"] is None

    with auth_session_factory() as session:
        campaign = session.scalar(select(Campaign))
        mutation_count = session.scalar(
            select(func.count()).select_from(ClientMutation)
        )
        quest_count = session.scalar(select(func.count()).select_from(Quest))
    assert campaign is not None
    assert campaign.user_id == UUID(str(registration["user"]["id"]))
    assert mutation_count == 1
    assert quest_count == 0


def test_create_campaign_assigns_deterministic_backend_order(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        first = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={"title": "First", "client_mutation_id": MUTATION_ID},
        )
        second = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={
                "title": "Second",
                "client_mutation_id": "40000000-0000-4000-8000-000000000002",
            },
        )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["display_order"] == 0
    assert second.json()["display_order"] == 1


def test_concurrent_exact_replay_creates_one_campaign(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
    headers = bearer(registration["access_token"])
    payload = {"title": "One result", "client_mutation_id": MUTATION_ID}

    def submit() -> tuple[int, dict[str, object]]:
        with create_auth_client(auth_database_url, auth_session_factory) as client:
            response = client.post(
                "/api/v1/campaigns",
                headers=headers,
                json=payload,
            )
            return response.status_code, response.json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: submit(), range(2)))

    assert [status for status, _ in results] == [201, 201]
    assert results[0][1] == results[1][1]
    with auth_session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Campaign)) == 1
        assert session.scalar(select(func.count()).select_from(ClientMutation)) == 1


def test_create_campaign_rejects_untrusted_fields_invalid_content_and_mutation_reuse(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        unauthenticated = client.post(
            "/api/v1/campaigns",
            json={"title": "Hidden", "client_mutation_id": MUTATION_ID},
        )
        blank = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={"title": "   ", "client_mutation_id": MUTATION_ID},
        )
        untrusted = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={
                "title": "Untrusted",
                "owner_id": registration["user"]["id"],
                "status": "completed",
                "record_version": 99,
                "client_mutation_id": MUTATION_ID,
            },
        )
        accepted = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={"title": "Accepted", "client_mutation_id": MUTATION_ID},
        )
        conflict = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={"title": "Different", "client_mutation_id": MUTATION_ID},
        )

    assert unauthenticated.status_code == 401
    assert blank.status_code == 422
    assert untrusted.status_code == 422
    assert accepted.status_code == 201
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "client_mutation_conflict"
