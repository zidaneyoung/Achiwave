from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import ClientMutation, Quest, QuestOccurrence, XpLedgerEntry
from tests.campaigns.helpers import bearer, create_auth_client, register


def _create_campaign(client, headers: dict[str, str]) -> dict[str, object]:
    response = client.post(
        "/api/v1/campaigns",
        headers=headers,
        json={
            "title": "Rewards",
            "client_mutation_id": "ef000000-0000-4000-8000-000000000001",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_allowed_reward_choices_are_authoritative_and_have_no_award_side_effect(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = _create_campaign(client, headers)
        created: list[dict[str, object]] = []
        version = int(campaign["record_version"])
        for index, reward in enumerate((0, 10, 20), start=2):
            response = client.post(
                f"/api/v1/campaigns/{campaign['id']}/quests",
                headers=headers,
                json={
                    "title": f"Reward {reward}",
                    "difficulty": "hard" if reward == 0 else "easy",
                    "reward_xp": reward,
                    "campaign_record_version": version,
                    "client_mutation_id": f"ef000000-0000-4000-8000-{index:012d}",
                },
            )
            assert response.status_code == 201
            created.append(response.json())
            version = response.json()["campaign_record_version"]

    assert [quest["reward_xp"] for quest in created] == [0, 10, 20]
    assert [quest["occurrence"]["reward_xp"] for quest in created] == [0, 10, 20]
    assert created[0]["difficulty"] == "hard"
    assert created[2]["difficulty"] == "easy"
    with auth_session_factory() as session:
        assert session.scalar(select(func.count()).select_from(XpLedgerEntry)) == 0


def test_new_rewards_reject_disallowed_negative_fractional_and_non_integer_values(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = _create_campaign(client, headers)
        responses = [
            client.post(
                f"/api/v1/campaigns/{campaign['id']}/quests",
                headers=headers,
                json={
                    "title": "Invalid reward",
                    "difficulty": "medium",
                    "reward_xp": reward,
                    "campaign_record_version": 1,
                    "client_mutation_id": mutation_id,
                },
            )
            for reward, mutation_id in [
                (5, "ef000000-0000-4000-8000-000000000010"),
                (-1, "ef000000-0000-4000-8000-000000000011"),
                (10.5, "ef000000-0000-4000-8000-000000000012"),
                ("10", "ef000000-0000-4000-8000-000000000013"),
                (999, "ef000000-0000-4000-8000-000000000014"),
            ]
        ]

    assert [response.status_code for response in responses] == [422] * 5
    with auth_session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Quest)) == 0
        assert session.scalar(select(func.count()).select_from(ClientMutation)) == 1


def test_legacy_reward_is_readable_but_only_allowed_changes_are_accepted(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = _create_campaign(client, headers)
        created = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=headers,
            json={
                "title": "Legacy reward",
                "difficulty": "medium",
                "reward_xp": 10,
                "campaign_record_version": 1,
                "client_mutation_id": "ef000000-0000-4000-8000-000000000020",
            },
        ).json()
        with auth_session_factory.begin() as session:
            quest = session.get(Quest, UUID(created["id"]))
            assert quest is not None
            quest.reward_xp = 25
        detail = client.get(f"/api/v1/quests/{created['id']}", headers=headers)
        stale = client.patch(
            f"/api/v1/quests/{created['id']}",
            headers=headers,
            json={
                "reward_xp": 20,
                "record_version": 999,
                "client_mutation_id": "ef000000-0000-4000-8000-000000000021",
            },
        )
        disallowed = client.patch(
            f"/api/v1/quests/{created['id']}",
            headers=headers,
            json={
                "reward_xp": 5,
                "record_version": created["record_version"],
                "client_mutation_id": "ef000000-0000-4000-8000-000000000022",
            },
        )
        same_legacy = client.patch(
            f"/api/v1/quests/{created['id']}",
            headers=headers,
            json={
                "reward_xp": 25,
                "record_version": created["record_version"],
                "client_mutation_id": "ef000000-0000-4000-8000-000000000023",
            },
        )
        unrelated = client.patch(
            f"/api/v1/quests/{created['id']}",
            headers=headers,
            json={
                "title": "Legacy reward renamed",
                "record_version": created["record_version"],
                "client_mutation_id": "ef000000-0000-4000-8000-000000000024",
            },
        )
        allowed = client.patch(
            f"/api/v1/quests/{created['id']}",
            headers=headers,
            json={
                "reward_xp": 20,
                "record_version": unrelated.json()["record_version"],
                "client_mutation_id": "ef000000-0000-4000-8000-000000000025",
            },
        )

    assert detail.status_code == 200 and detail.json()["reward_xp"] == 25
    assert stale.status_code == 409
    assert disallowed.status_code == 422
    assert disallowed.json()["code"] == "invalid_reward_xp"
    assert same_legacy.status_code == 200
    assert same_legacy.json()["reward_xp"] == 25
    assert same_legacy.json()["record_version"] == created["record_version"]
    assert unrelated.status_code == 200
    assert unrelated.json()["reward_xp"] == 25
    assert allowed.status_code == 200
    assert allowed.json()["reward_xp"] == 20
    assert allowed.json()["occurrence"] == created["occurrence"]
    with auth_session_factory() as session:
        occurrence = session.scalar(
            select(QuestOccurrence).where(
                QuestOccurrence.quest_id == UUID(created["id"])
            )
        )
        assert occurrence is not None and occurrence.reward_xp == 10
        assert session.scalar(select(func.count()).select_from(XpLedgerEntry)) == 0
