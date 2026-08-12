"""Destructive Stage 3 migration tests for an explicitly disposable PostgreSQL DB."""

import os
from pathlib import Path
from uuid import UUID

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from psycopg.types.json import Jsonb
from sqlalchemy.engine import make_url

from achiwave_backend.config import get_settings
from achiwave_backend.database import Base
import achiwave_backend.models  # noqa: F401

BACKEND_ROOT = Path(__file__).parents[1]
EXPECTED_HEAD = "20260812_0084"
TEST_DATABASE_ENV = "ACHIWAVE_TEST_DATABASE_URL"


def _test_database_url() -> str:
    database_url = os.environ.get(TEST_DATABASE_ENV)
    if database_url is None:
        pytest.skip(f"{TEST_DATABASE_ENV} is not configured")

    database_name = make_url(database_url).database or ""
    if not any(marker in database_name.lower() for marker in ("test", "stage3", "ci")):
        pytest.fail(
            f"Refusing destructive migration tests for unsafe database {database_name!r}"
        )
    return database_url


def _psycopg_url(database_url: str) -> str:
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def _alembic_config(database_url: str) -> Config:
    os.environ["ACHIWAVE_DATABASE_URL"] = database_url
    get_settings.cache_clear()
    return Config(str(BACKEND_ROOT / "alembic.ini"))


def _reset_to_head(database_url: str) -> Config:
    configuration = _alembic_config(database_url)
    command.downgrade(configuration, "base")
    command.upgrade(configuration, "head")
    return configuration


def _expect_constraint(
    cursor: psycopg.Cursor,
    constraint_name: str | set[str],
    statement: str,
    parameters: tuple[object, ...] = (),
) -> None:
    cursor.execute("SAVEPOINT invalid_record")
    try:
        cursor.execute(statement, parameters)
    except psycopg.IntegrityError as error:
        actual_name = error.diag.constraint_name
        cursor.execute("ROLLBACK TO SAVEPOINT invalid_record")
        expected_names = (
            {constraint_name} if isinstance(constraint_name, str) else constraint_name
        )
        assert actual_name in expected_names
    else:
        cursor.execute("ROLLBACK TO SAVEPOINT invalid_record")
        pytest.fail(f"Expected constraint {constraint_name} to reject the record")


def test_postgres_migration_lifecycle_and_metadata_consistency() -> None:
    database_url = _test_database_url()
    configuration = _reset_to_head(database_url)
    dsn = _psycopg_url(database_url)

    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT version_num FROM alembic_version")
        assert cursor.fetchone() == (EXPECTED_HEAD,)

        cursor.execute(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
        )
        assert {row[0] for row in cursor} == set(Base.metadata.tables)

    command.downgrade(configuration, "20260731_0001")
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT version_num FROM alembic_version")
        assert cursor.fetchone() == ("20260731_0001",)
        cursor.execute(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
        )
        assert cursor.fetchall() == []

    command.upgrade(configuration, "head")
    command.check(configuration)

    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT version_num FROM alembic_version")
        assert cursor.fetchone() == (EXPECTED_HEAD,)
        cursor.execute(
            "SELECT conname FROM pg_constraint WHERE connamespace = 'public'::regnamespace"
        )
        database_constraints = {row[0] for row in cursor}
        metadata_constraints = {
            constraint.name
            for table in Base.metadata.tables.values()
            for constraint in table.constraints
            if constraint.name is not None
        }
        assert metadata_constraints <= database_constraints


def test_postgres_rejects_critical_stage3_integrity_violations() -> None:
    database_url = _test_database_url()
    _reset_to_head(database_url)
    ids = {name: UUID(int=index) for index, name in enumerate(
        (
            "user_one", "user_two", "device_one", "device_two", "token_one",
            "campaign_one", "campaign_two", "quest_one", "quest_two",
            "quest_recurring", "occurrence_one", "occurrence_two",
            "occurrence_recurring", "mutation", "completion", "progress_event",
            "progress_probe", "ledger", "streak_day", "streak_source",
            "achievement", "rule", "achievement_progress", "unlock",
            "notification", "outbox", "delivery", "reminder", "evidence",
        ),
        start=1,
    )}
    dsn = _psycopg_url(database_url)

    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO users(id, canonical_email, display_email) VALUES "
            "(%s, 'one@example.com', 'one@example.com'), "
            "(%s, 'two@example.com', 'two@example.com')",
            (ids["user_one"], ids["user_two"]),
        )
        cursor.execute(
            "INSERT INTO user_preferences(user_id, timezone_name) "
            "VALUES (%s, 'America/Halifax')",
            (ids["user_one"],),
        )
        cursor.execute(
            "INSERT INTO registered_devices"
            "(id, user_id, platform, installation_id, app_environment) VALUES "
            "(%s, %s, 'android', 'installation-one', 'development'), "
            "(%s, %s, 'ios', 'installation-two', 'development')",
            (
                ids["device_one"],
                ids["user_one"],
                ids["device_two"],
                ids["user_two"],
            ),
        )
        cursor.execute(
            "INSERT INTO push_tokens"
            "(id, user_id, device_id, provider, platform, app_environment, "
            "token_value, token_hash) VALUES "
            "(%s, %s, %s, 'expo', 'android', 'development', 'private', %s)",
            (
                ids["token_one"],
                ids["user_one"],
                ids["device_one"],
                b"t" * 32,
            ),
        )
        cursor.execute(
            "INSERT INTO campaigns(id, user_id, title) VALUES "
            "(%s, %s, 'One'), (%s, %s, 'Two')",
            (
                ids["campaign_one"],
                ids["user_one"],
                ids["campaign_two"],
                ids["user_two"],
            ),
        )
        cursor.execute(
            "INSERT INTO quests"
            "(id, user_id, campaign_id, quest_type, title, reward_xp) VALUES "
            "(%s, %s, %s, 'one_time', 'One', 10), "
            "(%s, %s, %s, 'one_time', 'Two', 0), "
            "(%s, %s, %s, 'recurring', 'Daily', 1)",
            (
                ids["quest_one"], ids["user_one"], ids["campaign_one"],
                ids["quest_two"], ids["user_two"], ids["campaign_two"],
                ids["quest_recurring"], ids["user_one"], ids["campaign_one"],
            ),
        )
        cursor.execute(
            "INSERT INTO quest_recurrences"
            "(quest_id, user_id, campaign_id, quest_type, frequency, "
            "start_local_date, scheduled_local_time, timezone_name) "
            "VALUES (%s, %s, %s, 'recurring', 'daily', '2026-07-31', "
            "'08:00', 'America/Halifax')",
            (
                ids["quest_recurring"],
                ids["user_one"],
                ids["campaign_one"],
            ),
        )
        occurrence_sql = (
            "INSERT INTO quest_occurrences"
            "(id, user_id, campaign_id, quest_id, quest_type, occurrence_state, "
            "occurrence_local_date, scheduled_local_time, timezone_name, "
            "timezone_data_version, rule_version, available_at, reward_xp) "
            "VALUES (%s, %s, %s, %s, %s, 'available', %s, %s, "
            "'America/Halifax', '2026a', 1, now(), %s)"
        )
        cursor.execute(
            occurrence_sql,
            (
                ids["occurrence_one"], ids["user_one"], ids["campaign_one"],
                ids["quest_one"], "one_time", "2026-07-31", None, 10,
            ),
        )
        cursor.execute(
            occurrence_sql,
            (
                ids["occurrence_two"], ids["user_two"], ids["campaign_two"],
                ids["quest_two"], "one_time", "2026-07-31", None, 0,
            ),
        )
        cursor.execute(
            occurrence_sql,
            (
                ids["occurrence_recurring"], ids["user_one"],
                ids["campaign_one"], ids["quest_recurring"], "recurring",
                "2026-07-31", "08:00", 1,
            ),
        )
        cursor.execute(
            "INSERT INTO client_mutations"
            "(id, user_id, client_mutation_id, operation_type, payload_hash, "
            "target_type, target_id) VALUES (%s, %s, %s, 'complete_quest', %s, "
            "'quest', %s)",
            (
                UUID(int=100), ids["user_one"], ids["mutation"],
                b"m" * 32, ids["quest_one"],
            ),
        )
        cursor.execute(
            "INSERT INTO quest_completions"
            "(id, user_id, occurrence_id, client_mutation_id, "
            "completion_effective_date, event_sequence) "
            "VALUES (%s, %s, %s, %s, '2026-07-31', 1)",
            (
                ids["completion"], ids["user_one"], ids["occurrence_one"],
                ids["mutation"],
            ),
        )
        cursor.execute(
            "INSERT INTO progress_events"
            "(id, user_id, event_sequence, event_type, source_type, source_id, "
            "client_mutation_id, rule_version) VALUES "
            "(%s, %s, 10, 'completion_accepted', 'quest_completion', %s, %s, 1), "
            "(%s, %s, 11, 'probe', 'probe', %s, NULL, 1)",
            (
                ids["progress_event"], ids["user_one"], ids["completion"],
                ids["mutation"], ids["progress_probe"], ids["user_one"],
                UUID(int=101),
            ),
        )
        cursor.execute(
            "INSERT INTO xp_ledger_entries"
            "(id, user_id, xp_delta, reason, completion_id, progress_event_id, "
            "client_mutation_id, rule_version, event_sequence) "
            "VALUES (%s, %s, 10, 'quest_completion', %s, %s, %s, 1, 10)",
            (
                ids["ledger"], ids["user_one"], ids["completion"],
                ids["progress_event"], ids["mutation"],
            ),
        )
        cursor.execute(
            "INSERT INTO level_definitions"
            "(curve_version, level_number, minimum_total_xp) VALUES (1, 1, 0), (1, 2, 10)"
        )
        cursor.execute(
            "INSERT INTO streak_days"
            "(id, user_id, effective_local_date, timezone_name, "
            "timezone_preference_version, active_source_count) "
            "VALUES (%s, %s, '2026-07-31', 'America/Halifax', 1, 1)",
            (ids["streak_day"], ids["user_one"]),
        )
        cursor.execute(
            "INSERT INTO streak_day_sources"
            "(id, user_id, streak_day_id, completion_id, effective_local_date) "
            "VALUES (%s, %s, %s, %s, '2026-07-31')",
            (
                ids["streak_source"], ids["user_one"], ids["streak_day"],
                ids["completion"],
            ),
        )
        cursor.execute(
            "INSERT INTO achievement_definitions"
            "(id, definition_key, rule_version, visibility, progress_model, "
            "threshold_value, public_name, public_description, icon_key, "
            "accessible_label, definition_state, activated_at) "
            "VALUES (%s, 'complete_one', 1, 'visible', 'recalculable_counter', "
            "1, 'One', 'Complete one', 'complete-one', 'Complete one', 'active', now())",
            (ids["achievement"],),
        )
        cursor.execute(
            "INSERT INTO achievement_rules"
            "(id, achievement_definition_id, rule_version, rule_model, "
            "rule_configuration, authoritative_event_inputs, rule_schema_version, "
            "integrity_hash, activated_at) VALUES "
            "(%s, %s, 1, 'recalculable_counter', %s, %s, 1, %s, now())",
            (
                ids["rule"], ids["achievement"], Jsonb({"threshold": 1}),
                Jsonb(["completion_accepted"]), b"r" * 32,
            ),
        )
        cursor.execute(
            "INSERT INTO achievement_progress"
            "(id, user_id, achievement_definition_id, rule_version, progress_model, "
            "current_value, satisfaction_state, satisfied_at, "
            "last_progress_event_id, last_event_sequence) VALUES "
            "(%s, %s, %s, 1, 'recalculable_counter', 1, 'satisfied', now(), %s, 10)",
            (
                ids["achievement_progress"], ids["user_one"],
                ids["achievement"], ids["progress_event"],
            ),
        )
        cursor.execute(
            "INSERT INTO achievement_unlocks"
            "(id, user_id, achievement_definition_id, rule_version, "
            "achievement_progress_id, source_progress_event_id, "
            "source_progress_event_sequence, event_sequence) VALUES "
            "(%s, %s, %s, 1, %s, %s, 10, 20)",
            (
                ids["unlock"], ids["user_one"], ids["achievement"],
                ids["achievement_progress"], ids["progress_event"],
            ),
        )
        cursor.execute(
            "INSERT INTO notifications"
            "(id, user_id, notification_type, source_type, source_id, "
            "privacy_classification, content_mode, title, body) "
            "VALUES (%s, %s, 'quest_ready', 'quest', %s, 'private', "
            "'literal', 'Ready', 'Quest ready')",
            (ids["notification"], ids["user_one"], ids["quest_one"]),
        )
        cursor.execute(
            "INSERT INTO outbox_events"
            "(id, user_id, aggregate_type, aggregate_id, event_type, "
            "event_payload, event_schema_version) VALUES "
            "(%s, %s, 'notification', %s, 'notification.ready', %s, 1)",
            (
                ids["outbox"], ids["user_one"], ids["notification"],
                Jsonb({"notification_id": str(ids["notification"])}),
            ),
        )
        cursor.execute(
            "INSERT INTO notification_deliveries"
            "(id, notification_id, user_id, device_id, push_token_id, channel, "
            "provider, attempt_number, outbox_event_id) VALUES "
            "(%s, %s, %s, %s, %s, 'push', 'expo', 1, %s)",
            (
                ids["delivery"], ids["notification"], ids["user_one"],
                ids["device_one"], ids["token_one"], ids["outbox"],
            ),
        )
        cursor.execute(
            "INSERT INTO reminders"
            "(id, user_id, quest_id, occurrence_id, reminder_type, "
            "scheduled_local_time, timezone_name, timezone_preference_version) "
            "VALUES (%s, %s, %s, %s, 'before_occurrence', '08:00', "
            "'America/Halifax', 1)",
            (
                ids["reminder"], ids["user_one"], ids["quest_one"],
                ids["occurrence_one"],
            ),
        )
        cursor.execute(
            "INSERT INTO evidence_attachments"
            "(id, user_id, quest_id, occurrence_id, completion_id, "
            "storage_provider, storage_key, original_filename, media_type, "
            "byte_size, content_digest) VALUES "
            "(%s, %s, %s, %s, %s, 's3', 'objects/proof', 'proof.jpg', "
            "'image/jpeg', 1, %s)",
            (
                ids["evidence"], ids["user_one"], ids["quest_one"],
                ids["occurrence_one"], ids["completion"], b"e" * 32,
            ),
        )
        connection.commit()

        _expect_constraint(
            cursor,
            "uq_users_canonical_email",
            "INSERT INTO users(id, canonical_email, display_email) "
            "VALUES (%s, 'one@example.com', 'duplicate@example.com')",
            (UUID(int=200),),
        )
        _expect_constraint(
            cursor,
            "pk_user_preferences",
            "INSERT INTO user_preferences(user_id) VALUES (%s)",
            (ids["user_one"],),
        )
        _expect_constraint(
            cursor,
            "fk_device_sessions_device_user_registered_devices",
            "INSERT INTO device_sessions"
            "(id, user_id, device_id, session_state, expires_at) "
            "VALUES (%s, %s, %s, 'active', now() + interval '1 day')",
            (UUID(int=201), ids["user_two"], ids["device_one"]),
        )
        _expect_constraint(
            cursor,
            "fk_push_tokens_device_user_platform_environment",
            "INSERT INTO push_tokens"
            "(id, user_id, device_id, provider, platform, app_environment, "
            "token_value, token_hash) VALUES "
            "(%s, %s, %s, 'expo', 'android', 'development', 'cross', %s)",
            (UUID(int=202), ids["user_two"], ids["device_one"], b"x" * 32),
        )
        _expect_constraint(
            cursor,
            "fk_quests_campaign_user_campaigns",
            "INSERT INTO quests"
            "(id, user_id, campaign_id, quest_type, title) "
            "VALUES (%s, %s, %s, 'one_time', 'Cross')",
            (UUID(int=203), ids["user_two"], ids["campaign_one"]),
        )
        _expect_constraint(
            cursor,
            "fk_quest_occurrences_quest_owner_type",
            occurrence_sql,
            (
                UUID(int=204), ids["user_two"], ids["campaign_two"],
                ids["quest_recurring"], "one_time", "2026-08-01", None, 0,
            ),
        )
        _expect_constraint(
            cursor,
            "fk_quest_completions_occurrence_user",
            "INSERT INTO quest_completions"
            "(id, user_id, occurrence_id, completion_effective_date, event_sequence) "
            "VALUES (%s, %s, %s, '2026-07-31', 1)",
            (UUID(int=205), ids["user_two"], ids["occurrence_recurring"]),
        )
        _expect_constraint(
            cursor,
            "ck_quests_reward_xp_nonnegative",
            "UPDATE quests SET reward_xp = -1 WHERE id = %s",
            (ids["quest_one"],),
        )
        _expect_constraint(
            cursor,
            "ck_campaigns_campaign_state",
            "UPDATE campaigns SET campaign_state = 'unknown' WHERE id = %s",
            (ids["campaign_one"],),
        )
        _expect_constraint(
            cursor,
            "ck_quest_recurrences_frequency_fields",
            "UPDATE quest_recurrences SET frequency = 'weekly', weekly_days = NULL "
            "WHERE quest_id = %s",
            (ids["quest_recurring"],),
        )
        _expect_constraint(
            cursor,
            "uq_quest_occurrences_recurring_local_date",
            occurrence_sql,
            (
                UUID(int=206), ids["user_one"], ids["campaign_one"],
                ids["quest_recurring"], "recurring", "2026-07-31", "08:00", 1,
            ),
        )
        _expect_constraint(
            cursor,
            "uq_quest_completions_active_occurrence",
            "INSERT INTO quest_completions"
            "(id, user_id, occurrence_id, completion_effective_date, event_sequence) "
            "VALUES (%s, %s, %s, '2026-07-31', 2)",
            (UUID(int=207), ids["user_one"], ids["occurrence_one"]),
        )
        _expect_constraint(
            cursor,
            "uq_client_mutations_user_client_mutation",
            "INSERT INTO client_mutations"
            "(id, user_id, client_mutation_id, operation_type, payload_hash, "
            "target_type, target_id) VALUES "
            "(%s, %s, %s, 'complete_quest', %s, 'quest', %s)",
            (
                UUID(int=208), ids["user_one"], ids["mutation"],
                b"different" * 4, ids["quest_one"],
            ),
        )
        _expect_constraint(
            cursor,
            "uq_progress_events_user_sequence",
            "INSERT INTO progress_events"
            "(id, user_id, event_sequence, event_type, source_type, source_id) "
            "VALUES (%s, %s, 10, 'duplicate', 'probe', %s)",
            (UUID(int=209), ids["user_one"], UUID(int=210)),
        )
        _expect_constraint(
            cursor,
            "uq_xp_ledger_entries_completion_award",
            "INSERT INTO xp_ledger_entries"
            "(id, user_id, xp_delta, reason, completion_id, progress_event_id, "
            "rule_version, event_sequence) VALUES "
            "(%s, %s, 10, 'quest_completion', %s, %s, 1, 11)",
            (
                UUID(int=211), ids["user_one"], ids["completion"],
                ids["progress_probe"],
            ),
        )
        _expect_constraint(
            cursor,
            "ck_xp_ledger_entries_reason_source_delta",
            "INSERT INTO xp_ledger_entries"
            "(id, user_id, xp_delta, reason, completion_id, progress_event_id, "
            "rule_version, event_sequence) VALUES "
            "(%s, %s, -1, 'quest_completion', %s, %s, 1, 11)",
            (
                UUID(int=212), ids["user_one"], ids["completion"],
                ids["progress_probe"],
            ),
        )
        _expect_constraint(
            cursor,
            "ck_level_definitions_level_number_positive",
            "INSERT INTO level_definitions"
            "(curve_version, level_number, minimum_total_xp) VALUES (2, 0, 0)",
        )
        _expect_constraint(
            cursor,
            "uq_level_definitions_curve_threshold",
            "INSERT INTO level_definitions"
            "(curve_version, level_number, minimum_total_xp) VALUES (1, 3, 10)",
        )
        _expect_constraint(
            cursor,
            "uq_streak_days_user_date",
            "INSERT INTO streak_days"
            "(id, user_id, effective_local_date, timezone_name, "
            "timezone_preference_version, active_source_count) "
            "VALUES (%s, %s, '2026-07-31', 'UTC', 1, 1)",
            (UUID(int=213), ids["user_one"]),
        )
        _expect_constraint(
            cursor,
            "uq_achievement_unlocks_user_definition_version",
            "INSERT INTO achievement_unlocks"
            "(id, user_id, achievement_definition_id, rule_version, "
            "achievement_progress_id, source_progress_event_id, "
            "source_progress_event_sequence, event_sequence) VALUES "
            "(%s, %s, %s, 1, %s, %s, 10, 21)",
            (
                UUID(int=214), ids["user_one"], ids["achievement"],
                ids["achievement_progress"], ids["progress_event"],
            ),
        )
        _expect_constraint(
            cursor,
            "fk_notifications_user_id_users",
            "INSERT INTO notifications"
            "(id, user_id, notification_type, source_type, source_id, "
            "privacy_classification, content_mode, title, body) VALUES "
            "(%s, %s, 'probe', 'quest', %s, 'private', 'literal', 'T', 'B')",
            (UUID(int=215), UUID(int=999), ids["quest_one"]),
        )
        _expect_constraint(
            cursor,
            "fk_evidence_attachments_quest_user",
            "INSERT INTO evidence_attachments"
            "(id, user_id, quest_id, storage_provider, storage_key, "
            "original_filename, media_type, byte_size, content_digest) VALUES "
            "(%s, %s, %s, 's3', 'objects/cross', 'proof.jpg', 'image/jpeg', 1, %s)",
            (UUID(int=216), ids["user_two"], ids["quest_one"], b"z" * 32),
        )
        _expect_constraint(
            cursor,
            "ck_notification_deliveries_attempt_number_positive",
            "INSERT INTO notification_deliveries"
            "(id, notification_id, user_id, device_id, push_token_id, channel, "
            "provider, attempt_number, outbox_event_id) VALUES "
            "(%s, %s, %s, %s, %s, 'push', 'expo', 0, %s)",
            (
                UUID(int=217), ids["notification"], ids["user_one"],
                ids["device_one"], ids["token_one"], ids["outbox"],
            ),
        )
        _expect_constraint(
            cursor,
            "ck_outbox_events_attempt_count_nonnegative",
            "INSERT INTO outbox_events"
            "(id, user_id, aggregate_type, aggregate_id, event_type, "
            "event_payload, event_schema_version, attempt_count) VALUES "
            "(%s, %s, 'notification', %s, 'probe', %s, 1, -1)",
            (
                UUID(int=218), ids["user_one"], ids["notification"], Jsonb({}),
            ),
        )
        _expect_constraint(
            cursor,
            {
                "fk_evidence_attachments_occurrence_user",
                "fk_quest_completions_occurrence_user",
                "fk_reminders_occurrence_user",
            },
            "DELETE FROM quest_occurrences WHERE id = %s",
            (ids["occurrence_one"],),
        )

        cascade_user = UUID(int=219)
        cursor.execute(
            "INSERT INTO users(id, canonical_email, display_email) "
            "VALUES (%s, 'cascade@example.com', 'cascade@example.com')",
            (cascade_user,),
        )
        cursor.execute(
            "INSERT INTO user_preferences(user_id) VALUES (%s)",
            (cascade_user,),
        )
        cursor.execute("DELETE FROM users WHERE id = %s", (cascade_user,))
        cursor.execute(
            "SELECT count(*) FROM user_preferences WHERE user_id = %s",
            (cascade_user,),
        )
        assert cursor.fetchone() == (0,)

        cursor.execute("SELECT count(*) FROM xp_ledger_entries")
        assert cursor.fetchone() == (1,)
        cursor.execute("SELECT count(*) FROM achievement_unlocks")
        assert cursor.fetchone() == (1,)
        cursor.execute("SELECT count(*) FROM notification_deliveries")
        assert cursor.fetchone() == (1,)
