from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import Campaign, Quest
from tests.campaigns.helpers import bearer, create_auth_client, register, registration_payload


def create_campaign(session: Session, user_id: UUID, **overrides: object) -> Campaign:
    values: dict[str, object] = {
        "id": uuid4(),
        "user_id": user_id,
        "title": "Campaign",
        "display_order": 0,
        "campaign_state": "active",
    }
    values.update(overrides)
    campaign = Campaign(**values)
    session.add(campaign)
    session.flush()
    return campaign


def test_campaign_lists_separate_active_completed_and_archived_with_stable_order(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        user_id = UUID(str(registration["user"]["id"]))
        now = datetime.now(UTC)
        with auth_session_factory.begin() as session:
            second = create_campaign(
                session,
                user_id,
                title="Second active",
                display_order=2,
            )
            first = create_campaign(
                session,
                user_id,
                title="Completed first",
                display_order=1,
                campaign_state="completed",
                completed_at=now - timedelta(days=1),
            )
            archived = create_campaign(
                session,
                user_id,
                title="Archived",
                display_order=0,
                campaign_state="archived",
                archived_at=now,
            )
            session.add_all(
                [
                    Quest(
                        user_id=user_id,
                        campaign_id=first.id,
                        quest_type="one_time",
                        title="Active quest",
                        definition_state="active",
                        reward_xp=0,
                    ),
                    Quest(
                        user_id=user_id,
                        campaign_id=first.id,
                        quest_type="one_time",
                        title="Archived quest",
                        definition_state="archived",
                        archived_at=now,
                        reward_xp=0,
                    ),
                ]
            )
        headers = bearer(registration["access_token"])
        active_result = client.get("/api/v1/campaigns", headers=headers)
        archived_result = client.get(
            "/api/v1/campaigns?view=archived",
            headers=headers,
        )

    assert active_result.status_code == 200
    active_payload = active_result.json()
    assert [item["id"] for item in active_payload["items"]] == [
        str(first.id),
        str(second.id),
    ]
    assert [item["status"] for item in active_payload["items"]] == [
        "completed",
        "active",
    ]
    assert active_payload["items"][0]["quest_summary"] == {
        "active": 1,
        "archived": 1,
        "total": 2,
    }
    assert active_payload["total"] == 2
    assert archived_result.status_code == 200
    assert [item["id"] for item in archived_result.json()["items"]] == [
        str(archived.id)
    ]


def test_campaign_list_is_owner_scoped_paginated_and_validates_query(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        first_user = register(client)
        second_user = register(
            client,
            email="other@example.com",
            installation={
                **dict(registration_payload()["installation"]),
                "installation_id": "50000000-0000-4000-8000-000000000005",
            },
        )
        with auth_session_factory.begin() as session:
            for index in range(3):
                create_campaign(
                    session,
                    UUID(str(first_user["user"]["id"])),
                    title=f"First {index}",
                    display_order=index,
                )
            create_campaign(
                session,
                UUID(str(second_user["user"]["id"])),
                title="Private",
            )
        headers = bearer(first_user["access_token"])
        page = client.get(
            "/api/v1/campaigns?limit=1&offset=1",
            headers=headers,
        )
        invalid = client.get(
            "/api/v1/campaigns?view=all",
            headers=headers,
        )
        unauthenticated = client.get("/api/v1/campaigns")

    assert page.status_code == 200
    assert page.json()["total"] == 3
    assert len(page.json()["items"]) == 1
    assert page.json()["items"][0]["title"] == "First 1"
    assert invalid.status_code == 422
    assert unauthenticated.status_code == 401
