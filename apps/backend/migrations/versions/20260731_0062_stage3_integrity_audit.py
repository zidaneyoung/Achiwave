"""Complete Stage 3 constraint and foreign-key index audit.

Revision ID: 20260731_0062
Revises: 20260731_0061
Create Date: 2026-07-31
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260731_0062"
down_revision: str | Sequence[str] | None = "20260731_0061"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TIMEZONE_SHAPE = (
    "VALUE = 'UTC' OR VALUE ~ "
    "'^[A-Za-z]+([_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+(/[A-Za-z0-9_+-]+)*$'"
)
LEGACY_TIMEZONE_SHAPE = (
    "VALUE = 'UTC' OR VALUE ~ "
    "'^[A-Za-z]+(?:[_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+"
    "(?:/[A-Za-z0-9_+-]+)*$'"
)

TIMEZONE_CONSTRAINTS = (
    ("user_preferences", "ck_user_preferences_timezone_name_shape", "timezone_name"),
    ("quests", "ck_quests_one_time_timezone_shape", "one_time_timezone_name"),
    ("quest_recurrences", "ck_quest_recurrences_timezone_shape", "timezone_name"),
    ("quest_occurrences", "ck_quest_occurrences_timezone_shape", "timezone_name"),
    (
        "quest_completions",
        "ck_quest_completions_device_timezone_shape",
        "device_timezone_name",
    ),
    ("streak_days", "ck_streak_days_timezone_shape", "timezone_name"),
)

FK_INDEXES = (
    ("ix_achievement_progress_last_event", "achievement_progress", ["last_progress_event_id", "user_id", "last_event_sequence"]),
    ("ix_achievement_unlocks_progress", "achievement_unlocks", ["achievement_progress_id", "user_id"]),
    ("ix_achievement_unlocks_source_event", "achievement_unlocks", ["source_progress_event_id", "user_id", "source_progress_event_sequence"]),
    ("ix_device_sessions_replaced_by", "device_sessions", ["replaced_by_session_id", "user_id"]),
    ("ix_evidence_attachments_completion", "evidence_attachments", ["completion_id", "user_id", "occurrence_id"]),
    ("ix_notification_deliveries_device", "notification_deliveries", ["device_id", "user_id"]),
    ("ix_notification_deliveries_outbox", "notification_deliveries", ["outbox_event_id", "user_id"]),
    ("ix_notification_deliveries_push_token", "notification_deliveries", ["push_token_id", "user_id", "device_id", "provider"]),
    ("ix_outbox_events_user", "outbox_events", ["user_id"]),
    ("ix_progress_events_user_client_mutation", "progress_events", ["user_id", "client_mutation_id"]),
    ("ix_push_tokens_replaced_by", "push_tokens", ["replaced_by_push_token_id", "user_id", "device_id"]),
    ("ix_quest_completions_device", "quest_completions", ["device_id", "user_id"]),
    ("ix_quest_completion_reversals_device", "quest_completion_reversals", ["device_id", "user_id"]),
    ("ix_reminders_occurrence_owner", "reminders", ["occurrence_id", "user_id", "quest_id"]),
    ("ix_streak_day_sources_reversal", "streak_day_sources", ["reversal_id", "user_id", "completion_id"]),
    ("ix_synchronization_operations_device", "synchronization_operations", ["device_id", "user_id"]),
    ("ix_xp_ledger_entries_user_client_mutation", "xp_ledger_entries", ["user_id", "client_mutation_id"]),
)


def _timezone_expression(column: str, template: str) -> str:
    return template.replace("VALUE", column)


def upgrade() -> None:
    for table_name, constraint_name, column_name in TIMEZONE_CONSTRAINTS:
        op.drop_constraint(constraint_name, table_name, type_="check")
        op.create_check_constraint(
            constraint_name,
            table_name,
            _timezone_expression(column_name, TIMEZONE_SHAPE),
        )

    for index_name, table_name, columns in FK_INDEXES:
        op.create_index(index_name, table_name, columns, unique=False)


def downgrade() -> None:
    for index_name, table_name, _columns in reversed(FK_INDEXES):
        op.drop_index(index_name, table_name=table_name)

    for table_name, constraint_name, column_name in TIMEZONE_CONSTRAINTS:
        op.drop_constraint(constraint_name, table_name, type_="check")
        op.create_check_constraint(
            constraint_name,
            table_name,
            _timezone_expression(column_name, LEGACY_TIMEZONE_SHAPE),
        )
