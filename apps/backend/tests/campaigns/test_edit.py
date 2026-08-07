from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import Campaign, ClientMutation
from tests.campaigns.helpers import bearer, create_auth_client, register, registration_payload

MUTATION_ID = "80000000-0000-4000-8000-000000000008"


def test_campaign_edit_updates_only_content_with_version_and_exact_replay(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        created = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={
                "title": "Original",
                "client_mutation_id": "80000000-0000-4000-8000-000000000001",
            },
        ).json()
        payload = {
            "title": "  Updated  ",
            "description": "  New context  ",
            "record_version": created["record_version"],
            "client_mutation_id": MUTATION_ID,
        }
        updated = client.patch(
            f"/api/v1/campaigns/{created['id']}",
            headers=headers,
            json=payload,
        )
        replay = client.patch(
            f"/api/v1/campaigns/{created['id']}",
            headers=headers,
            json=payload,
        )

    assert updated.status_code == 200
    assert replay.status_code == 200
    assert updated.json() == replay.json()
    assert updated.json()["id"] == created["id"]
    assert updated.json()["title"] == "Updated"
    assert updated.json()["description"] == "New context"
    assert updated.json()["status"] == "active"
    assert updated.json()["record_version"] == 2
    assert updated.json()["updated_at"] != created["updated_at"]
    with auth_session_factory() as session:
        stored = session.get(Campaign, UUID(created["id"]))
        mutation_count = session.scalar(
            select(func.count())
            .select_from(ClientMutation)
            .where(ClientMutation.operation_type == "campaign_update")
        )
    assert stored is not None
    assert stored.user_id == UUID(str(registration["user"]["id"]))
    assert mutation_count == 1


def test_campaign_edit_returns_canonical_stale_conflict_and_rejects_untrusted_fields(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        created = client.post(
            "/api/v1/campaigns",
            headers=headers,
            json={
                "title": "Original",
                "client_mutation_id": "80000000-0000-4000-8000-000000000002",
            },
        ).json()
        accepted = client.patch(
            f"/api/v1/campaigns/{created['id']}",
            headers=headers,
            json={
                "title": "Current",
                "record_version": 1,
                "client_mutation_id": "80000000-0000-4000-8000-000000000003",
            },
        )
        stale = client.patch(
            f"/api/v1/campaigns/{created['id']}",
            headers=headers,
            json={
                "title": "Stale overwrite",
                "record_version": 1,
                "client_mutation_id": "80000000-0000-4000-8000-000000000004",
            },
        )
        untrusted = client.patch(
            f"/api/v1/campaigns/{created['id']}",
            headers=headers,
            json={
                "status": "completed",
                "record_version": 2,
                "client_mutation_id": "80000000-0000-4000-8000-000000000005",
            },
        )

    assert accepted.status_code == 200
    assert stale.status_code == 409
    assert stale.json()["code"] == "stale_record_version"
    assert stale.json()["current"]["title"] == "Current"
    assert stale.json()["current"]["record_version"] == 2
    assert untrusted.status_code == 422


def test_campaign_edit_hides_cross_user_identifier(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        first = register(client)
        second = register(
            client,
            email="editor@example.com",
            installation={
                **dict(registration_payload()["installation"]),
                "installation_id": "80000000-0000-4000-8000-000000000006",
            },
        )
        private = client.post(
            "/api/v1/campaigns",
            headers=bearer(second["access_token"]),
            json={
                "title": "Private",
                "client_mutation_id": "80000000-0000-4000-8000-000000000007",
            },
        ).json()
        response = client.patch(
            f"/api/v1/campaigns/{private['id']}",
            headers=bearer(first["access_token"]),
            json={
                "title": "Attack",
                "record_version": 1,
                "client_mutation_id": MUTATION_ID,
            },
        )

    assert response.status_code == 404
