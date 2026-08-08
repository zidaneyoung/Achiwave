from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from achiwave_backend.models import (
    AchievementDefinition,
    AchievementProgress,
    AchievementRule,
    AchievementUnlock,
    Campaign,
    ClientMutation,
    ProgressEvent,
    Quest,
    QuestCompletion,
    QuestCompletionReversal,
    QuestOccurrence,
    Streak,
    StreakDay,
    StreakDaySource,
    User,
    XpLedgerEntry,
)
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from tests.campaigns.helpers import (
    bearer,
    create_auth_client,
    register,
    registration_payload,
)


@dataclass(frozen=True)
class HistoricalGraph:
    owner_id: UUID
    campaign_id: UUID
    historical_quest_id: UUID
    unfinished_quest_id: UUID
    historical_occurrence_id: UUID
    unfinished_occurrence_id: UUID
    completion_id: UUID
    reversal_id: UUID
    completion_event_id: UUID
    reversal_event_id: UUID
    award_id: UUID
    compensation_id: UUID
    streak_day_id: UUID
    streak_source_id: UUID
    achievement_definition_id: UUID
    achievement_rule_id: UUID
    achievement_progress_id: UUID
    achievement_unlock_id: UUID
    effective_date: date


def _rows(session: Session, statement: object) -> tuple[tuple[object, ...], ...]:
    return tuple(tuple(row) for row in session.execute(statement))


def _historical_snapshot(
    session: Session,
    graph: HistoricalGraph,
) -> dict[str, tuple[tuple[object, ...], ...]]:
    quest_ids = (graph.historical_quest_id, graph.unfinished_quest_id)
    occurrence_ids = (
        graph.historical_occurrence_id,
        graph.unfinished_occurrence_id,
    )
    return {
        "quest_associations": _rows(
            session,
            select(Quest.id, Quest.user_id, Quest.campaign_id, Quest.quest_type)
            .where(Quest.id.in_(quest_ids))
            .order_by(Quest.id),
        ),
        "occurrences": _rows(
            session,
            select(
                QuestOccurrence.id,
                QuestOccurrence.user_id,
                QuestOccurrence.campaign_id,
                QuestOccurrence.quest_id,
                QuestOccurrence.quest_type,
                QuestOccurrence.occurrence_state,
                QuestOccurrence.occurrence_local_date,
                QuestOccurrence.timezone_name,
                QuestOccurrence.timezone_data_version,
                QuestOccurrence.rule_version,
                QuestOccurrence.available_at,
                QuestOccurrence.eligibility_expires_at,
                QuestOccurrence.reward_xp,
                QuestOccurrence.record_version,
                QuestOccurrence.completed_at,
                QuestOccurrence.reversed_at,
            )
            .where(QuestOccurrence.id.in_(occurrence_ids))
            .order_by(QuestOccurrence.id),
        ),
        "completions": _rows(
            session,
            select(
                QuestCompletion.id,
                QuestCompletion.user_id,
                QuestCompletion.occurrence_id,
                QuestCompletion.server_received_at,
                QuestCompletion.server_processed_at,
                QuestCompletion.completion_effective_date,
                QuestCompletion.event_sequence,
                QuestCompletion.reversed_at,
            ).where(QuestCompletion.id == graph.completion_id),
        ),
        "reversals": _rows(
            session,
            select(
                QuestCompletionReversal.id,
                QuestCompletionReversal.user_id,
                QuestCompletionReversal.occurrence_id,
                QuestCompletionReversal.completion_id,
                QuestCompletionReversal.reason,
                QuestCompletionReversal.server_received_at,
                QuestCompletionReversal.server_processed_at,
                QuestCompletionReversal.event_sequence,
            ).where(QuestCompletionReversal.id == graph.reversal_id),
        ),
        "ledger": _rows(
            session,
            select(
                XpLedgerEntry.id,
                XpLedgerEntry.user_id,
                XpLedgerEntry.xp_delta,
                XpLedgerEntry.reason,
                XpLedgerEntry.completion_id,
                XpLedgerEntry.reversal_id,
                XpLedgerEntry.progress_event_id,
                XpLedgerEntry.rule_version,
                XpLedgerEntry.source_award_amount,
                XpLedgerEntry.source_award_reason,
                XpLedgerEntry.reverses_ledger_entry_id,
                XpLedgerEntry.event_sequence,
            )
            .where(XpLedgerEntry.id.in_((graph.award_id, graph.compensation_id)))
            .order_by(XpLedgerEntry.event_sequence),
        ),
        "seeded_progress_events": _rows(
            session,
            select(
                ProgressEvent.id,
                ProgressEvent.user_id,
                ProgressEvent.event_sequence,
                ProgressEvent.event_type,
                ProgressEvent.source_type,
                ProgressEvent.source_id,
                ProgressEvent.effective_local_date,
                ProgressEvent.rule_version,
                ProgressEvent.event_metadata,
            )
            .where(
                ProgressEvent.id.in_(
                    (graph.completion_event_id, graph.reversal_event_id)
                )
            )
            .order_by(ProgressEvent.event_sequence),
        ),
        "streak": _rows(
            session,
            select(
                Streak.user_id,
                Streak.current_streak_days,
                Streak.longest_streak_days,
                Streak.last_qualifying_local_date,
                Streak.calculated_through_event_sequence,
                Streak.record_version,
            ).where(Streak.user_id == graph.owner_id),
        ),
        "streak_days": _rows(
            session,
            select(
                StreakDay.id,
                StreakDay.user_id,
                StreakDay.effective_local_date,
                StreakDay.timezone_name,
                StreakDay.timezone_preference_version,
                StreakDay.credit_state,
                StreakDay.active_source_count,
                StreakDay.credited_at,
                StreakDay.removed_at,
            ).where(StreakDay.id == graph.streak_day_id),
        ),
        "streak_sources": _rows(
            session,
            select(
                StreakDaySource.id,
                StreakDaySource.user_id,
                StreakDaySource.streak_day_id,
                StreakDaySource.completion_id,
                StreakDaySource.reversal_id,
                StreakDaySource.effective_local_date,
                StreakDaySource.source_state,
                StreakDaySource.contributed_at,
                StreakDaySource.reversed_at,
            ).where(StreakDaySource.id == graph.streak_source_id),
        ),
        "achievement_definitions": _rows(
            session,
            select(
                AchievementDefinition.id,
                AchievementDefinition.definition_key,
                AchievementDefinition.rule_version,
                AchievementDefinition.visibility,
                AchievementDefinition.progress_model,
                AchievementDefinition.threshold_value,
                AchievementDefinition.definition_state,
                AchievementDefinition.activated_at,
            ).where(AchievementDefinition.id == graph.achievement_definition_id),
        ),
        "achievement_rules": _rows(
            session,
            select(
                AchievementRule.id,
                AchievementRule.achievement_definition_id,
                AchievementRule.rule_version,
                AchievementRule.rule_model,
                AchievementRule.rule_configuration,
                AchievementRule.authoritative_event_inputs,
                AchievementRule.rule_schema_version,
                AchievementRule.integrity_hash,
            ).where(AchievementRule.id == graph.achievement_rule_id),
        ),
        "achievement_progress": _rows(
            session,
            select(
                AchievementProgress.id,
                AchievementProgress.user_id,
                AchievementProgress.achievement_definition_id,
                AchievementProgress.rule_version,
                AchievementProgress.progress_model,
                AchievementProgress.current_value,
                AchievementProgress.progress_state,
                AchievementProgress.satisfaction_state,
                AchievementProgress.satisfied_at,
                AchievementProgress.last_progress_event_id,
                AchievementProgress.last_event_sequence,
                AchievementProgress.record_version,
            ).where(AchievementProgress.id == graph.achievement_progress_id),
        ),
        "achievement_unlocks": _rows(
            session,
            select(
                AchievementUnlock.id,
                AchievementUnlock.user_id,
                AchievementUnlock.achievement_definition_id,
                AchievementUnlock.rule_version,
                AchievementUnlock.achievement_progress_id,
                AchievementUnlock.source_progress_event_id,
                AchievementUnlock.source_progress_event_sequence,
                AchievementUnlock.event_sequence,
                AchievementUnlock.unlocked_at,
            ).where(AchievementUnlock.id == graph.achievement_unlock_id),
        ),
    }


def _seed_populated_history(
    auth_session_factory: sessionmaker[Session],
    owner_id: UUID,
) -> HistoricalGraph:
    created_at = datetime.now(UTC).replace(microsecond=0) - timedelta(days=3)
    completed_at = created_at + timedelta(days=1)
    reversed_at = completed_at + timedelta(days=1)
    effective_date = completed_at.date()

    graph = HistoricalGraph(
        owner_id=owner_id,
        campaign_id=uuid4(),
        historical_quest_id=uuid4(),
        unfinished_quest_id=uuid4(),
        historical_occurrence_id=uuid4(),
        unfinished_occurrence_id=uuid4(),
        completion_id=uuid4(),
        reversal_id=uuid4(),
        completion_event_id=uuid4(),
        reversal_event_id=uuid4(),
        award_id=uuid4(),
        compensation_id=uuid4(),
        streak_day_id=uuid4(),
        streak_source_id=uuid4(),
        achievement_definition_id=uuid4(),
        achievement_rule_id=uuid4(),
        achievement_progress_id=uuid4(),
        achievement_unlock_id=uuid4(),
        effective_date=effective_date,
    )

    with auth_session_factory.begin() as session:
        user = session.get(User, owner_id)
        assert user is not None
        user.next_event_sequence = 3

        campaign = Campaign(
            id=graph.campaign_id,
            user_id=owner_id,
            title="History campaign",
            display_order=0,
            campaign_state="active",
            record_version=1,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(campaign)
        session.flush()

        historical_quest = Quest(
            id=graph.historical_quest_id,
            user_id=owner_id,
            campaign_id=graph.campaign_id,
            quest_type="one_time",
            definition_state="active",
            title="Historical quest",
            difficulty="medium",
            reward_xp=20,
            display_order=0,
            record_version=1,
            created_at=created_at,
            updated_at=created_at,
        )
        unfinished_quest = Quest(
            id=graph.unfinished_quest_id,
            user_id=owner_id,
            campaign_id=graph.campaign_id,
            quest_type="one_time",
            definition_state="active",
            title="Unfinished sibling",
            difficulty="easy",
            reward_xp=0,
            display_order=1,
            record_version=1,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add_all([historical_quest, unfinished_quest])
        session.flush()

        historical_occurrence = QuestOccurrence(
            id=graph.historical_occurrence_id,
            user_id=owner_id,
            campaign_id=graph.campaign_id,
            quest_id=graph.historical_quest_id,
            quest_type="one_time",
            occurrence_state="reversed",
            occurrence_local_date=effective_date,
            timezone_name="America/Halifax",
            timezone_data_version="test",
            rule_version=1,
            available_at=created_at,
            reward_xp=20,
            generated_at=created_at,
            record_version=3,
            completed_at=completed_at,
            reversed_at=reversed_at,
            created_at=created_at,
            updated_at=reversed_at,
        )
        unfinished_occurrence = QuestOccurrence(
            id=graph.unfinished_occurrence_id,
            user_id=owner_id,
            campaign_id=graph.campaign_id,
            quest_id=graph.unfinished_quest_id,
            quest_type="one_time",
            occurrence_state="available",
            occurrence_local_date=effective_date,
            timezone_name="America/Halifax",
            timezone_data_version="test",
            rule_version=1,
            available_at=created_at,
            reward_xp=0,
            generated_at=created_at,
            record_version=1,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add_all([historical_occurrence, unfinished_occurrence])
        session.flush()

        completion = QuestCompletion(
            id=graph.completion_id,
            user_id=owner_id,
            occurrence_id=graph.historical_occurrence_id,
            server_received_at=completed_at,
            server_processed_at=completed_at,
            completion_effective_date=effective_date,
            event_sequence=1,
            reversed_at=reversed_at,
            created_at=completed_at,
        )
        session.add(completion)
        session.flush()

        reversal = QuestCompletionReversal(
            id=graph.reversal_id,
            user_id=owner_id,
            occurrence_id=graph.historical_occurrence_id,
            completion_id=graph.completion_id,
            reason="Correct historical completion",
            server_received_at=reversed_at,
            server_processed_at=reversed_at,
            event_sequence=2,
            created_at=reversed_at,
        )
        session.add(reversal)
        session.flush()

        completion_event = ProgressEvent(
            id=graph.completion_event_id,
            user_id=owner_id,
            event_sequence=1,
            event_type="completion_accepted",
            source_type="quest_completion",
            source_id=graph.completion_id,
            server_received_at=completed_at,
            server_processed_at=completed_at,
            effective_local_date=effective_date,
            rule_version=1,
            event_metadata={"quest_id": str(graph.historical_quest_id)},
            created_at=completed_at,
        )
        reversal_event = ProgressEvent(
            id=graph.reversal_event_id,
            user_id=owner_id,
            event_sequence=2,
            event_type="completion_reversed",
            source_type="quest_completion_reversal",
            source_id=graph.reversal_id,
            server_received_at=reversed_at,
            server_processed_at=reversed_at,
            effective_local_date=effective_date,
            rule_version=1,
            event_metadata={"quest_id": str(graph.historical_quest_id)},
            created_at=reversed_at,
        )
        session.add_all([completion_event, reversal_event])
        session.flush()

        award = XpLedgerEntry(
            id=graph.award_id,
            user_id=owner_id,
            xp_delta=20,
            reason="quest_completion",
            completion_id=graph.completion_id,
            progress_event_id=graph.completion_event_id,
            rule_version=1,
            event_sequence=1,
            server_recorded_at=completed_at,
            created_at=completed_at,
        )
        session.add(award)
        session.flush()
        session.add(
            XpLedgerEntry(
                id=graph.compensation_id,
                user_id=owner_id,
                xp_delta=-20,
                reason="completion_reversal",
                reversal_id=graph.reversal_id,
                progress_event_id=graph.reversal_event_id,
                rule_version=1,
                source_award_amount=20,
                source_award_reason="quest_completion",
                reverses_ledger_entry_id=graph.award_id,
                event_sequence=2,
                server_recorded_at=reversed_at,
                created_at=reversed_at,
            )
        )
        session.flush()

        streak_day = StreakDay(
            id=graph.streak_day_id,
            user_id=owner_id,
            effective_local_date=effective_date,
            timezone_name="America/Halifax",
            timezone_preference_version=1,
            credit_state="removed",
            active_source_count=0,
            credited_at=completed_at,
            removed_at=reversed_at,
            created_at=completed_at,
            updated_at=reversed_at,
        )
        session.add_all(
            [
                Streak(
                    user_id=owner_id,
                    current_streak_days=0,
                    longest_streak_days=1,
                    calculated_through_event_sequence=2,
                    record_version=2,
                    created_at=completed_at,
                    updated_at=reversed_at,
                ),
                streak_day,
            ]
        )
        session.flush()
        session.add(
            StreakDaySource(
                id=graph.streak_source_id,
                user_id=owner_id,
                streak_day_id=graph.streak_day_id,
                completion_id=graph.completion_id,
                reversal_id=graph.reversal_id,
                effective_local_date=effective_date,
                source_state="reversed",
                contributed_at=completed_at,
                reversed_at=reversed_at,
                created_at=completed_at,
            )
        )
        session.flush()

        definition = AchievementDefinition(
            id=graph.achievement_definition_id,
            definition_key=(
                f"historical_completion_{graph.achievement_definition_id.hex}"
            ),
            rule_version=1,
            visibility="visible",
            progress_model="recalculable_counter",
            threshold_value=1,
            public_name="Historical completion",
            public_description="Complete one quest.",
            icon_key="historical-completion",
            accessible_label="Historical completion achievement",
            progress_exposure_enabled=True,
            retroactive_evaluation_enabled=True,
            definition_state="active",
            activated_at=created_at,
            created_at=created_at,
        )
        session.add(definition)
        session.flush()
        session.add(
            AchievementRule(
                id=graph.achievement_rule_id,
                achievement_definition_id=graph.achievement_definition_id,
                rule_version=1,
                rule_model="recalculable_counter",
                rule_configuration={"threshold": 1},
                authoritative_event_inputs=["completion_accepted"],
                rule_schema_version=1,
                integrity_hash=b"history-integrity-rule-hash-0001",
                created_at=created_at,
                activated_at=created_at,
            )
        )
        session.flush()

        achievement_progress = AchievementProgress(
            id=graph.achievement_progress_id,
            user_id=owner_id,
            achievement_definition_id=graph.achievement_definition_id,
            rule_version=1,
            progress_model="recalculable_counter",
            current_value=0,
            progress_state={"active_completion_count": 0},
            satisfaction_state="unsatisfied",
            last_progress_event_id=graph.reversal_event_id,
            last_event_sequence=2,
            record_version=2,
            created_at=completed_at,
            updated_at=reversed_at,
        )
        session.add(achievement_progress)
        session.flush()
        session.add(
            AchievementUnlock(
                id=graph.achievement_unlock_id,
                user_id=owner_id,
                achievement_definition_id=graph.achievement_definition_id,
                rule_version=1,
                achievement_progress_id=graph.achievement_progress_id,
                source_progress_event_id=graph.completion_event_id,
                source_progress_event_sequence=1,
                event_sequence=1,
                unlocked_at=completed_at,
                created_at=completed_at,
            )
        )

    return graph


def _post_transition_with_immediate_replay(
    client: object,
    path: str,
    headers: dict[str, str],
    *,
    record_version: int,
) -> tuple[dict[str, object], dict[str, object]]:
    payload: dict[str, object] = {
        "record_version": record_version,
        "client_mutation_id": str(uuid4()),
    }
    first = client.post(path, headers=headers, json=payload)
    replay = client.post(path, headers=headers, json=payload)
    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()
    return payload, first.json()


def _assert_delete_is_restricted(
    auth_session_factory: sessionmaker[Session],
    statement: object,
    *,
    constraint_name: str,
) -> None:
    with auth_session_factory() as session:
        with pytest.raises(IntegrityError) as captured:
            session.execute(statement)
            session.commit()
        session.rollback()
    assert captured.value.orig.diag.constraint_name == constraint_name


def test_archive_restore_replays_preserve_authorized_history_and_restrict_deletes(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        owner = register(client)
        other = register(
            client,
            email="history-other@example.com",
            installation={
                **dict(registration_payload()["installation"]),
                "installation_id": "92000000-0000-4000-8000-000000000129",
            },
        )
        owner_id = UUID(str(owner["user"]["id"]))
        graph = _seed_populated_history(auth_session_factory, owner_id)
        with auth_session_factory() as session:
            before = _historical_snapshot(session, graph)

        owner_headers = bearer(owner["access_token"])
        other_headers = bearer(other["access_token"])
        quest_path = f"/api/v1/quests/{graph.historical_quest_id}"
        campaign_path = f"/api/v1/campaigns/{graph.campaign_id}"

        quest_archive_one_payload, quest_archive_one = (
            _post_transition_with_immediate_replay(
                client,
                f"{quest_path}/archive",
                owner_headers,
                record_version=1,
            )
        )
        assert quest_archive_one["definition_state"] == "archived"
        assert quest_archive_one["record_version"] == 2
        assert quest_archive_one["campaign_record_version"] == 2

        default_detail = client.get(campaign_path, headers=owner_headers)
        historical_detail = client.get(
            f"{campaign_path}?include_archived_quests=true",
            headers=owner_headers,
        )
        default_quests = client.get("/api/v1/quests", headers=owner_headers)
        archived_quests = client.get(
            "/api/v1/quests?status=archived",
            headers=owner_headers,
        )
        archived_quest_detail = client.get(quest_path, headers=owner_headers)
        assert default_detail.status_code == 200
        assert [item["id"] for item in default_detail.json()["quests"]] == [
            str(graph.unfinished_quest_id)
        ]
        assert historical_detail.status_code == 200
        assert {item["id"] for item in historical_detail.json()["quests"]} == {
            str(graph.historical_quest_id),
            str(graph.unfinished_quest_id),
        }
        assert default_quests.status_code == 200
        assert [item["id"] for item in default_quests.json()["items"]] == [
            str(graph.unfinished_quest_id)
        ]
        assert archived_quests.status_code == 200
        assert [item["id"] for item in archived_quests.json()["items"]] == [
            str(graph.historical_quest_id)
        ]
        assert archived_quest_detail.status_code == 200
        assert archived_quest_detail.json()["definition_state"] == "archived"

        assert client.get(campaign_path, headers=other_headers).status_code == 404
        assert client.get(quest_path, headers=other_headers).status_code == 404
        other_archived_quests = client.get(
            "/api/v1/quests?status=archived",
            headers=other_headers,
        )
        assert other_archived_quests.status_code == 200
        assert other_archived_quests.json()["items"] == []

        quest_restore_one_payload, quest_restore_one = (
            _post_transition_with_immediate_replay(
                client,
                f"{quest_path}/restore",
                owner_headers,
                record_version=2,
            )
        )
        assert quest_restore_one["definition_state"] == "active"
        assert quest_restore_one["record_version"] == 3
        assert quest_restore_one["campaign_record_version"] == 3

        delayed_quest_archive = client.post(
            f"{quest_path}/archive",
            headers=owner_headers,
            json=quest_archive_one_payload,
        )
        assert delayed_quest_archive.status_code == 200
        assert delayed_quest_archive.json() == quest_archive_one
        current_quest = client.get(quest_path, headers=owner_headers)
        assert current_quest.status_code == 200
        assert current_quest.json()["definition_state"] == "active"
        assert current_quest.json()["record_version"] == 3

        _, quest_archive_two = _post_transition_with_immediate_replay(
            client,
            f"{quest_path}/archive",
            owner_headers,
            record_version=3,
        )
        assert quest_archive_two["definition_state"] == "archived"
        assert quest_archive_two["record_version"] == 4
        delayed_quest_restore = client.post(
            f"{quest_path}/restore",
            headers=owner_headers,
            json=quest_restore_one_payload,
        )
        assert delayed_quest_restore.status_code == 200
        assert delayed_quest_restore.json() == quest_restore_one
        current_quest = client.get(quest_path, headers=owner_headers)
        assert current_quest.json()["definition_state"] == "archived"
        assert current_quest.json()["record_version"] == 4

        _, quest_restore_two = _post_transition_with_immediate_replay(
            client,
            f"{quest_path}/restore",
            owner_headers,
            record_version=4,
        )
        assert quest_restore_two["definition_state"] == "active"
        assert quest_restore_two["record_version"] == 5
        assert quest_restore_two["campaign_record_version"] == 5

        campaign_archive_one_payload, campaign_archive_one = (
            _post_transition_with_immediate_replay(
                client,
                f"{campaign_path}/archive",
                owner_headers,
                record_version=5,
            )
        )
        assert campaign_archive_one["status"] == "archived"
        assert campaign_archive_one["record_version"] == 6

        active_campaigns = client.get("/api/v1/campaigns", headers=owner_headers)
        archived_campaigns = client.get(
            "/api/v1/campaigns?view=archived",
            headers=owner_headers,
        )
        hidden_with_campaign = client.get("/api/v1/quests", headers=owner_headers)
        archived_campaign_detail = client.get(campaign_path, headers=owner_headers)
        archived_parent_quest_detail = client.get(quest_path, headers=owner_headers)
        assert active_campaigns.status_code == 200
        assert active_campaigns.json()["items"] == []
        assert archived_campaigns.status_code == 200
        assert [item["id"] for item in archived_campaigns.json()["items"]] == [
            str(graph.campaign_id)
        ]
        assert hidden_with_campaign.status_code == 200
        assert hidden_with_campaign.json()["items"] == []
        assert archived_campaign_detail.status_code == 200
        assert archived_campaign_detail.json()["status"] == "archived"
        assert {item["id"] for item in archived_campaign_detail.json()["quests"]} == {
            str(graph.historical_quest_id),
            str(graph.unfinished_quest_id),
        }
        assert archived_parent_quest_detail.status_code == 200
        assert archived_parent_quest_detail.json()["campaign_status"] == "archived"

        other_archived_campaigns = client.get(
            "/api/v1/campaigns?view=archived",
            headers=other_headers,
        )
        assert other_archived_campaigns.status_code == 200
        assert other_archived_campaigns.json()["items"] == []
        assert client.get(campaign_path, headers=other_headers).status_code == 404
        assert client.get(quest_path, headers=other_headers).status_code == 404

        campaign_restore_one_payload, campaign_restore_one = (
            _post_transition_with_immediate_replay(
                client,
                f"{campaign_path}/restore",
                owner_headers,
                record_version=6,
            )
        )
        assert campaign_restore_one["status"] == "active"
        assert campaign_restore_one["record_version"] == 7

        delayed_campaign_archive = client.post(
            f"{campaign_path}/archive",
            headers=owner_headers,
            json=campaign_archive_one_payload,
        )
        assert delayed_campaign_archive.status_code == 200
        assert delayed_campaign_archive.json() == campaign_archive_one
        current_campaign = client.get(campaign_path, headers=owner_headers)
        assert current_campaign.status_code == 200
        assert current_campaign.json()["status"] == "active"
        assert current_campaign.json()["record_version"] == 7

        _, campaign_archive_two = _post_transition_with_immediate_replay(
            client,
            f"{campaign_path}/archive",
            owner_headers,
            record_version=7,
        )
        assert campaign_archive_two["status"] == "archived"
        assert campaign_archive_two["record_version"] == 8
        delayed_campaign_restore = client.post(
            f"{campaign_path}/restore",
            headers=owner_headers,
            json=campaign_restore_one_payload,
        )
        assert delayed_campaign_restore.status_code == 200
        assert delayed_campaign_restore.json() == campaign_restore_one
        current_campaign = client.get(campaign_path, headers=owner_headers)
        assert current_campaign.json()["status"] == "archived"
        assert current_campaign.json()["record_version"] == 8

        _, campaign_restore_two = _post_transition_with_immediate_replay(
            client,
            f"{campaign_path}/restore",
            owner_headers,
            record_version=8,
        )
        assert campaign_restore_two["status"] == "active"
        assert campaign_restore_two["record_version"] == 9

        final_campaigns = client.get("/api/v1/campaigns", headers=owner_headers)
        final_quests = client.get("/api/v1/quests", headers=owner_headers)
        assert [item["id"] for item in final_campaigns.json()["items"]] == [
            str(graph.campaign_id)
        ]
        assert {item["id"] for item in final_quests.json()["items"]} == {
            str(graph.historical_quest_id),
            str(graph.unfinished_quest_id),
        }

    with auth_session_factory() as session:
        after = _historical_snapshot(session, graph)
        assert after == before

        campaign = session.get(Campaign, graph.campaign_id)
        historical_quest = session.get(Quest, graph.historical_quest_id)
        unfinished_quest = session.get(Quest, graph.unfinished_quest_id)
        user = session.get(User, graph.owner_id)
        assert campaign is not None
        assert campaign.campaign_state == "active"
        assert campaign.record_version == 9
        assert historical_quest is not None
        assert historical_quest.definition_state == "active"
        assert historical_quest.record_version == 5
        assert historical_quest.campaign_id == graph.campaign_id
        assert unfinished_quest is not None
        assert unfinished_quest.definition_state == "active"
        assert unfinished_quest.record_version == 1
        assert unfinished_quest.campaign_id == graph.campaign_id
        assert user is not None and user.next_event_sequence == 11

        assert (
            session.scalar(
                select(func.count())
                .select_from(QuestOccurrence)
                .where(QuestOccurrence.user_id == graph.owner_id)
            )
            == 2
        )
        assert (
            session.scalar(
                select(func.count())
                .select_from(QuestCompletion)
                .where(QuestCompletion.user_id == graph.owner_id)
            )
            == 1
        )
        assert (
            session.scalar(
                select(func.count())
                .select_from(QuestCompletionReversal)
                .where(QuestCompletionReversal.user_id == graph.owner_id)
            )
            == 1
        )
        assert (
            session.scalar(
                select(func.sum(XpLedgerEntry.xp_delta)).where(
                    XpLedgerEntry.user_id == graph.owner_id
                )
            )
            == 0
        )

        events = session.execute(
            select(
                ProgressEvent.event_sequence,
                ProgressEvent.event_type,
                ProgressEvent.source_type,
                ProgressEvent.event_metadata,
            )
            .where(ProgressEvent.user_id == graph.owner_id)
            .order_by(ProgressEvent.event_sequence)
        ).all()
        assert [(sequence, event_type) for sequence, event_type, _, _ in events] == [
            (1, "completion_accepted"),
            (2, "completion_reversed"),
            (3, "quest_archived"),
            (4, "quest_restored"),
            (5, "quest_archived"),
            (6, "quest_restored"),
            (7, "campaign_archived"),
            (8, "campaign_restored"),
            (9, "campaign_archived"),
            (10, "campaign_restored"),
        ]
        for _, event_type, source_type, metadata in events[2:]:
            assert source_type == "client_mutation"
            assert metadata["campaign_id"] == str(graph.campaign_id)
            if event_type.startswith("quest_"):
                assert metadata["quest_id"] == str(graph.historical_quest_id)

        mutation_rows = session.execute(
            select(ClientMutation.operation_type, ClientMutation.result_payload).where(
                ClientMutation.user_id == graph.owner_id
            )
        ).all()
        assert Counter(operation for operation, _ in mutation_rows) == {
            "one_time_quest_archive": 2,
            "one_time_quest_restore": 2,
            "campaign_archive": 2,
            "campaign_restore": 2,
        }
        assert all(result_payload is not None for _, result_payload in mutation_rows)

        progress = session.get(AchievementProgress, graph.achievement_progress_id)
        unlock = session.get(AchievementUnlock, graph.achievement_unlock_id)
        streak_day = session.get(StreakDay, graph.streak_day_id)
        streak_source = session.get(StreakDaySource, graph.streak_source_id)
        assert progress is not None
        assert progress.current_value == 0
        assert progress.satisfaction_state == "unsatisfied"
        assert unlock is not None and unlock.id == graph.achievement_unlock_id
        assert streak_day is not None and streak_day.credit_state == "removed"
        assert streak_day.active_source_count == 0
        assert streak_source is not None and streak_source.source_state == "reversed"

    _assert_delete_is_restricted(
        auth_session_factory,
        delete(Quest).where(Quest.id == graph.historical_quest_id),
        constraint_name="fk_quest_occurrences_quest_owner_type",
    )
    _assert_delete_is_restricted(
        auth_session_factory,
        delete(Campaign).where(Campaign.id == graph.campaign_id),
        constraint_name="fk_quests_campaign_user_campaigns",
    )

    with auth_session_factory() as session:
        assert session.get(Campaign, graph.campaign_id) is not None
        assert session.get(Quest, graph.historical_quest_id) is not None
        assert _historical_snapshot(session, graph) == before
