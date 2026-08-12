from tests.campaigns.helpers import bearer, create_auth_client, register


def create_campaign_and_quest(client, headers, *, title: str = "Finish launch"):
    campaign_response = client.post(
        "/api/v1/campaigns",
        headers=headers,
        json={
            "title": "Stage 7 campaign",
            "client_mutation_id": "d0000000-0000-4000-8000-000000000001",
        },
    )
    assert campaign_response.status_code == 201
    campaign = campaign_response.json()
    quest_response = client.post(
        f"/api/v1/campaigns/{campaign['id']}/quests",
        headers=headers,
        json={
            "title": title,
            "difficulty": "medium",
            "reward_xp": 20,
            "campaign_record_version": campaign["record_version"],
            "client_mutation_id": "d0000000-0000-4000-8000-000000000002",
        },
    )
    assert quest_response.status_code == 201
    return campaign, quest_response.json()


__all__ = [
    "bearer",
    "create_auth_client",
    "create_campaign_and_quest",
    "register",
]
