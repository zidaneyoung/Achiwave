from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import ProgressEvent, User, XpLedgerEntry
from tests.completions.helpers import (
    bearer,
    create_auth_client,
    create_campaign_and_quest,
    register,
)


def test_completion_and_reversal_append_ordered_source_events_without_rewards(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        headers = bearer(registration["access_token"])
        _, quest = create_campaign_and_quest(client, headers)
        complete_payload = {
            "client_mutation_id": "d3000000-0000-4000-8000-000000000001",
            "expected_occurrence_version": 1,
        }
        completed = client.post(
            f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete",
            headers=headers,
            json=complete_payload,
        )
        completion_replay = client.post(
            f"/api/v1/quest-occurrences/{quest['occurrence']['id']}/complete",
            headers=headers,
            json=complete_payload,
        )
        reverse_payload = {
            "client_mutation_id": "d3000000-0000-4000-8000-000000000002",
            "expected_occurrence_version": 2,
            "reason": "user_correction",
        }
        reversed_response = client.post(
            f"/api/v1/quest-completions/{completed.json()['completion']['id']}/reverse",
            headers=headers,
            json=reverse_payload,
        )
        reversal_replay = client.post(
            f"/api/v1/quest-completions/{completed.json()['completion']['id']}/reverse",
            headers=headers,
            json=reverse_payload,
        )

    assert completed.status_code == 200
    assert reversed_response.status_code == 200
    assert completion_replay.json() == completed.json()
    assert reversal_replay.json() == reversed_response.json()
    assert [
        (event["event_sequence"], event["event_type"])
        for event in completed.json()["progress_events"]
    ] == [(1, "completion_accepted"), (2, "campaign_completed")]
    assert [
        (event["event_sequence"], event["event_type"])
        for event in reversed_response.json()["progress_events"]
    ] == [(3, "completion_reversed"), (4, "campaign_reopened")]

    with auth_session_factory() as session:
        events = list(
            session.scalars(select(ProgressEvent).order_by(ProgressEvent.event_sequence))
        )
        assert [event.event_sequence for event in events] == [1, 2, 3, 4]
        assert [event.event_type for event in events] == [
            "completion_accepted",
            "campaign_completed",
            "completion_reversed",
            "campaign_reopened",
        ]
        assert len({event.id for event in events}) == 4
        assert events[0].source_type == "quest_completion"
        assert events[0].source_id == UUID(completed.json()["completion"]["id"])
        assert events[2].source_type == "quest_completion_reversal"
        assert events[2].source_id == UUID(reversed_response.json()["reversal"]["id"])
        assert all(event.rule_version == 1 for event in events)
        user = session.scalar(select(User))
        assert user is not None and user.next_event_sequence == 5
        assert session.scalar(select(func.count()).select_from(XpLedgerEntry)) == 0
