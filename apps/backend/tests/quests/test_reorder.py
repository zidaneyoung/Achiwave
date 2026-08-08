from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import ClientMutation, ProgressEvent, Quest, XpLedgerEntry
from tests.campaigns.helpers import (
    bearer,
    create_auth_client,
    register,
    registration_payload,
)


def _campaign(client, headers: dict[str, str], *, suffix: str) -> dict[str, object]:
    response = client.post(
        "/api/v1/campaigns",
        headers=headers,
        json={
            "title": f"Order {suffix}",
            "client_mutation_id": f"f1000000-0000-4000-8000-{suffix:0>12}",
        },
    )
    assert response.status_code == 201
    return response.json()


def _quests(
    client,
    headers: dict[str, str],
    campaign: dict[str, object],
    *,
    prefix: int,
    count: int = 3,
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    campaign_version = int(campaign["record_version"])
    for offset in range(count):
        response = client.post(
            f"/api/v1/campaigns/{campaign['id']}/quests",
            headers=headers,
            json={
                "title": f"Quest {prefix + offset}",
                "difficulty": "medium",
                "reward_xp": 10,
                "campaign_record_version": campaign_version,
                "client_mutation_id": (
                    f"f2000000-0000-4000-8000-{prefix + offset:012d}"
                ),
            },
        )
        assert response.status_code == 201
        result.append(response.json())
        campaign_version = response.json()["campaign_record_version"]
    return result


def _item(quest: dict[str, object]) -> dict[str, object]:
    return {"id": quest["id"], "record_version": quest["record_version"]}


def test_reorder_is_canonical_transactional_and_replay_safe(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = _campaign(client, headers, suffix="101")
        quests = _quests(client, headers, campaign, prefix=100)
        payload = {
            "items": [_item(quests[2]), _item(quests[0]), _item(quests[1])],
            "campaign_record_version": quests[-1]["campaign_record_version"],
            "client_mutation_id": "f3000000-0000-4000-8000-000000000001",
        }
        reordered = client.put(
            f"/api/v1/campaigns/{campaign['id']}/quests/order",
            headers=headers,
            json=payload,
        )
        replay = client.put(
            f"/api/v1/campaigns/{campaign['id']}/quests/order",
            headers=headers,
            json=payload,
        )
        mutation_reuse = client.put(
            f"/api/v1/campaigns/{campaign['id']}/quests/order",
            headers=headers,
            json={
                **payload,
                "items": [_item(quests[0]), _item(quests[1]), _item(quests[2])],
            },
        )
        detail = client.get(f"/api/v1/campaigns/{campaign['id']}", headers=headers)

    assert reordered.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == reordered.json()
    assert mutation_reuse.status_code == 409
    result = reordered.json()
    assert [item["id"] for item in result["items"]] == [
        quests[2]["id"],
        quests[0]["id"],
        quests[1]["id"],
    ]
    assert [item["display_order"] for item in result["items"]] == [0, 1, 2]
    assert result["campaign_record_version"] == 5
    assert [quest["id"] for quest in detail.json()["quests"]] == [
        item["id"] for item in result["items"]
    ]
    with auth_session_factory() as session:
        assert session.scalar(
            select(func.count())
            .select_from(ClientMutation)
            .where(ClientMutation.operation_type == "active_quest_reorder")
        ) == 1
        assert session.scalar(select(func.count()).select_from(ProgressEvent)) == 0
        assert session.scalar(select(func.count()).select_from(XpLedgerEntry)) == 0


def test_exact_reorder_replay_returns_original_result_after_later_reorder(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = _campaign(client, headers, suffix="102")
        quests = _quests(client, headers, campaign, prefix=110)
        original_payload = {
            "items": [_item(quests[2]), _item(quests[0]), _item(quests[1])],
            "campaign_record_version": quests[-1]["campaign_record_version"],
            "client_mutation_id": "f3000000-0000-4000-8000-000000000002",
        }
        original = client.put(
            f"/api/v1/campaigns/{campaign['id']}/quests/order",
            headers=headers,
            json=original_payload,
        )
        original_result = original.json()
        original_items = {
            item["id"]: item for item in original_result["items"]
        }
        later = client.put(
            f"/api/v1/campaigns/{campaign['id']}/quests/order",
            headers=headers,
            json={
                "items": [
                    _item(original_items[quest["id"]])
                    for quest in quests
                ],
                "campaign_record_version": original_result[
                    "campaign_record_version"
                ],
                "client_mutation_id": "f3000000-0000-4000-8000-000000000003",
            },
        )
        detail = client.get(f"/api/v1/campaigns/{campaign['id']}", headers=headers)
        archived = client.post(
            f"/api/v1/campaigns/{campaign['id']}/archive",
            headers=headers,
            json={
                "record_version": later.json()["campaign_record_version"],
                "client_mutation_id": "f3000000-0000-4000-8000-000000000004",
            },
        )
        delayed_replay = client.put(
            f"/api/v1/campaigns/{campaign['id']}/quests/order",
            headers=headers,
            json=original_payload,
        )

    assert original.status_code == 200
    assert later.status_code == 200
    assert archived.status_code == 200
    assert delayed_replay.status_code == 200
    assert delayed_replay.json() == original_result
    assert delayed_replay.json() != later.json()
    assert [quest["id"] for quest in detail.json()["quests"]] == [
        item["id"] for item in later.json()["items"]
    ]
    with auth_session_factory() as session:
        stored = session.scalar(
            select(ClientMutation).where(
                ClientMutation.client_mutation_id
                == UUID("f3000000-0000-4000-8000-000000000002")
            )
        )
        assert stored is not None
        assert stored.result_payload == original_result


def test_reorder_rejects_duplicate_missing_unknown_archived_and_cross_campaign_ids(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = _campaign(client, headers, suffix="201")
        quests = _quests(client, headers, campaign, prefix=200)
        other_campaign = _campaign(client, headers, suffix="202")
        other_quest = _quests(
            client,
            headers,
            other_campaign,
            prefix=220,
            count=1,
        )[0]
        second = register(
            client,
            email="quest-order-owner@example.com",
            installation={
                **dict(registration_payload()["installation"]),
                "installation_id": "f5000000-0000-4000-8000-000000000001",
            },
        )
        second_headers = bearer(second["access_token"])
        second_campaign = _campaign(client, second_headers, suffix="203")
        second_quest = _quests(
            client,
            second_headers,
            second_campaign,
            prefix=230,
            count=1,
        )[0]
        campaign_version = quests[-1]["campaign_record_version"]
        cases = [
            [_item(quests[0]), _item(quests[0]), _item(quests[2])],
            [_item(quests[0]), _item(quests[1])],
            [
                _item(quests[0]),
                _item(quests[1]),
                {
                    "id": "f4000000-0000-4000-8000-000000000099",
                    "record_version": 1,
                },
            ],
            [_item(quests[0]), _item(quests[1]), _item(other_quest)],
            [_item(quests[0]), _item(quests[1]), _item(second_quest)],
        ]
        invalid = [
            client.put(
                f"/api/v1/campaigns/{campaign['id']}/quests/order",
                headers=headers,
                json={
                    "items": items,
                    "campaign_record_version": campaign_version,
                    "client_mutation_id": (
                        f"f3000000-0000-4000-8000-{index:012d}"
                    ),
                },
            )
            for index, items in enumerate(cases, start=10)
        ]
        archived = client.post(
            f"/api/v1/quests/{quests[1]['id']}/archive",
            headers=headers,
            json={
                "record_version": quests[1]["record_version"],
                "client_mutation_id": "f3000000-0000-4000-8000-000000000020",
            },
        ).json()
        archived_id = client.put(
            f"/api/v1/campaigns/{campaign['id']}/quests/order",
            headers=headers,
            json={
                "items": [_item(quests[0]), _item(quests[1]), _item(quests[2])],
                "campaign_record_version": archived["campaign_record_version"],
                "client_mutation_id": "f3000000-0000-4000-8000-000000000021",
            },
        )

    assert [response.status_code for response in invalid] == [422, 422, 422, 422, 422]
    assert [response.json().get("code") for response in invalid[1:]] == [
        "invalid_quest_order",
        "invalid_quest_order",
        "invalid_quest_order",
        "invalid_quest_order",
    ]
    assert archived_id.status_code == 422
    assert archived_id.json()["code"] == "invalid_quest_order"


def test_reorder_rejects_stale_versions_and_serializes_concurrent_writes(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = _campaign(client, headers, suffix="301")
        quests = _quests(client, headers, campaign, prefix=300)
        campaign_version = quests[-1]["campaign_record_version"]
        stale_campaign = client.put(
            f"/api/v1/campaigns/{campaign['id']}/quests/order",
            headers=headers,
            json={
                "items": [_item(quest) for quest in quests],
                "campaign_record_version": campaign_version - 1,
                "client_mutation_id": "f3000000-0000-4000-8000-000000000030",
            },
        )
        stale_items = [_item(quest) for quest in quests]
        stale_items[1] = {**stale_items[1], "record_version": 99}
        stale_quest = client.put(
            f"/api/v1/campaigns/{campaign['id']}/quests/order",
            headers=headers,
            json={
                "items": stale_items,
                "campaign_record_version": campaign_version,
                "client_mutation_id": "f3000000-0000-4000-8000-000000000031",
            },
        )

    orders = ([quests[2], quests[1], quests[0]], [quests[1], quests[0], quests[2]])

    def submit(index: int) -> tuple[int, dict[str, object]]:
        with create_auth_client(auth_database_url, auth_session_factory) as client:
            response = client.put(
                f"/api/v1/campaigns/{campaign['id']}/quests/order",
                headers=headers,
                json={
                    "items": [_item(quest) for quest in orders[index]],
                    "campaign_record_version": campaign_version,
                    "client_mutation_id": (
                        f"f3000000-0000-4000-8000-{40 + index:012d}"
                    ),
                },
            )
            return response.status_code, response.json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        concurrent = list(executor.map(submit, range(2)))

    assert stale_campaign.status_code == 409
    assert stale_quest.status_code == 409
    assert sorted(status_code for status_code, _ in concurrent) == [200, 409]
    conflict = next(body for status_code, body in concurrent if status_code == 409)
    assert conflict["code"] == "stale_record_version"
    assert [item["display_order"] for item in conflict["current"]["items"]] == [0, 1, 2]


def test_restored_quest_appends_after_current_active_order(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        campaign = _campaign(client, headers, suffix="401")
        quests = _quests(client, headers, campaign, prefix=400)
        archived = client.post(
            f"/api/v1/quests/{quests[1]['id']}/archive",
            headers=headers,
            json={
                "record_version": quests[1]["record_version"],
                "client_mutation_id": "f3000000-0000-4000-8000-000000000050",
            },
        ).json()
        reordered = client.put(
            f"/api/v1/campaigns/{campaign['id']}/quests/order",
            headers=headers,
            json={
                "items": [_item(quests[2]), _item(quests[0])],
                "campaign_record_version": archived["campaign_record_version"],
                "client_mutation_id": "f3000000-0000-4000-8000-000000000051",
            },
        ).json()
        restored = client.post(
            f"/api/v1/quests/{quests[1]['id']}/restore",
            headers=headers,
            json={
                "record_version": archived["record_version"],
                "client_mutation_id": "f3000000-0000-4000-8000-000000000052",
            },
        )
        detail = client.get(f"/api/v1/campaigns/{campaign['id']}", headers=headers)

    assert [item["display_order"] for item in reordered["items"]] == [0, 1]
    assert restored.status_code == 200
    assert restored.json()["display_order"] == 2
    assert [quest["id"] for quest in detail.json()["quests"]] == [
        quests[2]["id"],
        quests[0]["id"],
        quests[1]["id"],
    ]
    with auth_session_factory() as session:
        stored = session.get(Quest, UUID(quests[1]["id"]))
        assert stored is not None and stored.display_order == 2
