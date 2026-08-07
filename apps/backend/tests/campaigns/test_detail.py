from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import Campaign, Quest
from tests.campaigns.helpers import bearer, create_auth_client, register, registration_payload


def test_campaign_detail_returns_owner_campaign_and_explicit_archived_quest_view(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    now = datetime.now(UTC)
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        user_id = UUID(str(registration["user"]["id"]))
        with auth_session_factory.begin() as session:
            campaign = Campaign(
                user_id=user_id,
                title="Detailed campaign",
                description="Canonical detail",
                campaign_state="archived",
                archived_at=now,
            )
            session.add(campaign)
            session.flush()
            session.add_all(
                [
                    Quest(
                        user_id=user_id,
                        campaign_id=campaign.id,
                        quest_type="one_time",
                        title="Active quest",
                        definition_state="active",
                        reward_xp=10,
                        display_order=1,
                    ),
                    Quest(
                        user_id=user_id,
                        campaign_id=campaign.id,
                        quest_type="one_time",
                        title="Archived quest",
                        definition_state="archived",
                        archived_at=now,
                        reward_xp=20,
                        display_order=2,
                    ),
                ]
            )
        headers = bearer(registration["access_token"])
        default = client.get(f"/api/v1/campaigns/{campaign.id}", headers=headers)
        with_archived = client.get(
            f"/api/v1/campaigns/{campaign.id}?include_archived_quests=true",
            headers=headers,
        )

    assert default.status_code == 200
    assert default.json()["status"] == "archived"
    assert default.json()["description"] == "Canonical detail"
    assert [quest["title"] for quest in default.json()["quests"]] == [
        "Active quest"
    ]
    assert default.json()["quests"][0]["status"] == "active"
    assert default.json()["quest_summary"] == {
        "active": 1,
        "archived": 1,
        "total": 2,
    }
    assert [quest["title"] for quest in with_archived.json()["quests"]] == [
        "Active quest",
        "Archived quest",
    ]
    assert with_archived.json()["quest_summary"] == {
        "active": 1,
        "archived": 1,
        "total": 2,
    }


def test_campaign_detail_hides_cross_user_and_unknown_identifiers(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        first = register(client)
        second = register(
            client,
            email="private@example.com",
            installation={
                **dict(registration_payload()["installation"]),
                "installation_id": "60000000-0000-4000-8000-000000000006",
            },
        )
        with auth_session_factory.begin() as session:
            private = Campaign(
                user_id=UUID(str(second["user"]["id"])),
                title="Private",
            )
            session.add(private)
            session.flush()
        headers = bearer(first["access_token"])
        cross_user = client.get(
            f"/api/v1/campaigns/{private.id}",
            headers=headers,
        )
        unknown = client.get(
            "/api/v1/campaigns/70000000-0000-4000-8000-000000000007",
            headers=headers,
        )

    assert cross_user.status_code == 404
    assert unknown.status_code == 404
    assert cross_user.json() == unknown.json()
