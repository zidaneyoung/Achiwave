from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID, uuid4

from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import (
    Campaign,
    Quest,
    QuestOccurrence,
    QuestRecurrence,
    UserPreference,
)
from tests.campaigns.helpers import (
    bearer,
    create_auth_client,
    register,
    registration_payload,
)


def _campaign(
    session: Session,
    user_id: UUID,
    title: str,
    *,
    display_order: int = 0,
    archived: bool = False,
) -> Campaign:
    campaign = Campaign(
        id=uuid4(),
        user_id=user_id,
        title=title,
        display_order=display_order,
        campaign_state="archived" if archived else "active",
        archived_at=datetime.now(UTC) if archived else None,
    )
    session.add(campaign)
    session.flush()
    return campaign


def _quest(
    session: Session,
    user_id: UUID,
    campaign: Campaign,
    title: str,
    *,
    status: str = "available",
    category: str | None = None,
    due_at: datetime | None = None,
    display_order: int = 0,
    recurring: bool = False,
) -> Quest:
    now = datetime.now(UTC)
    archived = status == "archived"
    quest = Quest(
        id=uuid4(),
        user_id=user_id,
        campaign_id=campaign.id,
        quest_type="recurring" if recurring else "one_time",
        definition_state="archived" if archived else "active",
        title=title,
        category=category,
        difficulty="medium",
        reward_xp=10,
        display_order=display_order,
        due_at=None if recurring else due_at,
        one_time_timezone_name=(
            "America/Halifax" if due_at is not None and not recurring else None
        ),
        archived_at=now if archived else None,
    )
    session.add(quest)
    session.flush()
    occurrence_state = "available" if archived or recurring else status
    occurrence = QuestOccurrence(
        id=uuid4(),
        user_id=user_id,
        campaign_id=campaign.id,
        quest_id=quest.id,
        quest_type=quest.quest_type,
        occurrence_state=occurrence_state,
        occurrence_local_date=date(2026, 8, 8),
        scheduled_local_time=time(9, 0) if recurring else None,
        timezone_name="America/Halifax",
        timezone_data_version="test",
        rule_version=1,
        available_at=now - timedelta(days=1),
        eligibility_expires_at=due_at,
        reward_xp=10,
        completed_at=now if occurrence_state == "completed" else None,
        reversed_at=now if occurrence_state == "reversed" else None,
        expired_at=now if occurrence_state == "expired" else None,
        voided_at=now if occurrence_state == "voided" else None,
    )
    session.add(occurrence)
    if recurring:
        session.add(
            QuestRecurrence(
                quest_id=quest.id,
                user_id=user_id,
                campaign_id=campaign.id,
                quest_type="recurring",
                frequency="daily",
                start_local_date=date(2026, 8, 8),
                scheduled_local_time=time(9, 0),
                timezone_name="America/Halifax",
            )
        )
    return quest


def test_quest_list_is_owner_scoped_paginated_and_hides_archived_by_default(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        owner = register(client)
        other = register(
            client,
            email="quest-list-other@example.com",
            installation={
                **dict(registration_payload()["installation"]),
                "installation_id": "91000000-0000-4000-8000-000000000091",
            },
        )
        owner_id = UUID(str(owner["user"]["id"]))
        other_id = UUID(str(other["user"]["id"]))
        with auth_session_factory.begin() as session:
            later_campaign = _campaign(
                session, owner_id, "Later campaign", display_order=2
            )
            first_campaign = _campaign(
                session, owner_id, "First campaign", display_order=1
            )
            archived_campaign = _campaign(
                session,
                owner_id,
                "Archived campaign",
                display_order=3,
                archived=True,
            )
            private_campaign = _campaign(session, other_id, "Private campaign")
            first = _quest(
                session,
                owner_id,
                first_campaign,
                "First quest",
                display_order=0,
            )
            second = _quest(
                session,
                owner_id,
                first_campaign,
                "Second quest",
                display_order=1,
            )
            third = _quest(
                session,
                owner_id,
                later_campaign,
                "Later quest",
                display_order=0,
            )
            archived = _quest(
                session, owner_id, first_campaign, "Archived quest", status="archived"
            )
            _quest(session, owner_id, archived_campaign, "Hidden with campaign")
            archived_with_campaign = _quest(
                session,
                owner_id,
                archived_campaign,
                "Archived with campaign",
                status="archived",
            )
            _quest(session, other_id, private_campaign, "Private quest")

        headers = bearer(owner["access_token"])
        default = client.get("/api/v1/quests", headers=headers)
        page = client.get("/api/v1/quests?limit=1&offset=1", headers=headers)
        archived_result = client.get(
            "/api/v1/quests?status=archived", headers=headers
        )
        cross_owner = client.get(
            f"/api/v1/quests?campaign_id={private_campaign.id}", headers=headers
        )
        unauthenticated = client.get("/api/v1/quests")

    assert default.status_code == 200
    payload = default.json()
    assert [item["id"] for item in payload["items"]] == [
        str(first.id),
        str(second.id),
        str(third.id),
    ]
    assert payload["items"][0]["campaign_title"] == "First campaign"
    assert payload["items"][0]["status"] == "available"
    assert payload["total"] == 3
    assert page.status_code == 200
    assert page.json()["total"] == 3
    assert [item["id"] for item in page.json()["items"]] == [str(second.id)]
    assert archived_result.status_code == 200
    assert [item["id"] for item in archived_result.json()["items"]] == [
        str(archived.id),
        str(archived_with_campaign.id),
    ]
    assert cross_owner.status_code == 200
    assert cross_owner.json()["items"] == []
    assert cross_owner.json()["total"] == 0
    assert unauthenticated.status_code == 401


def test_quest_list_filters_every_canonical_status_and_validates_values(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        owner = register(client)
        owner_id = UUID(str(owner["user"]["id"]))
        with auth_session_factory.begin() as session:
            campaign = _campaign(session, owner_id, "Statuses")
            expected = {
                "active": _quest(
                    session, owner_id, campaign, "Recurring", recurring=True
                ),
                "archived": _quest(
                    session, owner_id, campaign, "Archived", status="archived"
                ),
            }
            for occurrence_status in (
                "scheduled",
                "available",
                "completed",
                "reversed",
                "expired",
                "voided",
            ):
                expected[occurrence_status] = _quest(
                    session,
                    owner_id,
                    campaign,
                    occurrence_status.title(),
                    status=occurrence_status,
                )

        headers = bearer(owner["access_token"])
        results = {
            quest_status: client.get(
                f"/api/v1/quests?status={quest_status}", headers=headers
            )
            for quest_status in expected
        }
        invalid_status = client.get(
            "/api/v1/quests?status=pending", headers=headers
        )
        invalid_category = client.get(
            "/api/v1/quests?category=Health", headers=headers
        )
        invalid_campaign = client.get(
            "/api/v1/quests?campaign_id=not-a-uuid", headers=headers
        )
        invalid_date = client.get(
            "/api/v1/quests?due_from=08-08-2026", headers=headers
        )
        reversed_range = client.get(
            "/api/v1/quests?due_from=2030-07-03&due_to=2030-07-02",
            headers=headers,
        )
        maximum_end_date = client.get(
            "/api/v1/quests?due_to=9999-12-31", headers=headers
        )

    for quest_status, result in results.items():
        assert result.status_code == 200
        assert [item["id"] for item in result.json()["items"]] == [
            str(expected[quest_status].id)
        ]
        assert result.json()["items"][0]["status"] == quest_status
    assert invalid_status.status_code == 422
    assert invalid_category.status_code == 422
    assert invalid_campaign.status_code == 422
    assert invalid_date.status_code == 422
    assert reversed_range.status_code == 422
    assert reversed_range.json()["code"] == "invalid_due_date_range"
    assert maximum_end_date.status_code == 200


def test_quest_list_combines_campaign_category_status_and_local_due_range(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        owner = register(client)
        owner_id = UUID(str(owner["user"]["id"]))
        with auth_session_factory.begin() as session:
            preference = session.get(UserPreference, owner_id)
            assert preference is not None
            preference.timezone_name = "America/Halifax"
            campaign = _campaign(session, owner_id, "Target")
            other_campaign = _campaign(session, owner_id, "Other")
            # July 2-3 in Halifax is [July 2 03:00Z, July 4 03:00Z).
            included_start = _quest(
                session,
                owner_id,
                campaign,
                "Start boundary",
                category="health",
                due_at=datetime(2030, 7, 2, 3, 0, tzinfo=UTC),
            )
            included_end = _quest(
                session,
                owner_id,
                campaign,
                "End boundary",
                category="health",
                due_at=datetime(2030, 7, 4, 2, 59, tzinfo=UTC),
                display_order=1,
            )
            _quest(
                session,
                owner_id,
                campaign,
                "Before",
                category="health",
                due_at=datetime(2030, 7, 2, 2, 59, tzinfo=UTC),
            )
            _quest(
                session,
                owner_id,
                campaign,
                "After",
                category="health",
                due_at=datetime(2030, 7, 4, 3, 0, tzinfo=UTC),
            )
            _quest(
                session,
                owner_id,
                campaign,
                "Wrong category",
                category="work",
                due_at=datetime(2030, 7, 3, 12, 0, tzinfo=UTC),
            )
            _quest(
                session,
                owner_id,
                campaign,
                "Wrong status",
                status="completed",
                category="health",
                due_at=datetime(2030, 7, 3, 12, 0, tzinfo=UTC),
            )
            _quest(
                session,
                owner_id,
                other_campaign,
                "Wrong campaign",
                category="health",
                due_at=datetime(2030, 7, 3, 12, 0, tzinfo=UTC),
            )
            uncategorized = _quest(
                session,
                owner_id,
                campaign,
                "Uncategorized",
                due_at=datetime(2030, 7, 3, 12, 0, tzinfo=UTC),
            )

        headers = bearer(owner["access_token"])
        combined = client.get(
            "/api/v1/quests",
            headers=headers,
            params={
                "campaign_id": str(campaign.id),
                "status": "available",
                "category": "health",
                "due_from": "2030-07-02",
                "due_to": "2030-07-03",
            },
        )
        uncategorized_result = client.get(
            "/api/v1/quests",
            headers=headers,
            params={"campaign_id": str(campaign.id), "category": "uncategorized"},
        )

    assert combined.status_code == 200
    assert [item["id"] for item in combined.json()["items"]] == [
        str(included_start.id),
        str(included_end.id),
    ]
    assert combined.json()["total"] == 2
    assert uncategorized_result.status_code == 200
    assert [item["id"] for item in uncategorized_result.json()["items"]] == [
        str(uncategorized.id)
    ]
