# Stage 3 acceptance audit

Stage 3 covers database-schema and data-integrity issues #37–#64 only. This
evidence was collected on 2026-07-31 against PostgreSQL 18.4. Issue #65 starts
Stage 4 and remains outside this implementation.

## Result

All technical acceptance criteria for issues #37–#64 pass. Revisions form one
linear chain from the empty Stage 2 baseline `20260731_0001` to
`20260731_0062`. A disposable PostgreSQL database completed base-to-head,
head-to-baseline, and baseline-to-head migration paths; metadata drift and the
critical invalid-record probes passed.

## Publication evidence

| Key | Branch | Pull request | Merge commit |
|---|---|---|---|
| B1 | `stage-3/identity-devices-37-41` | [#374](https://github.com/zidaneyoung/Achiwave/pull/374) | `b3c0e942028cd67a08567f0b599a382aeb530426` |
| B2 | `stage-3/campaign-quest-schema-42-46` | [#375](https://github.com/zidaneyoung/Achiwave/pull/375) | `48829578d5ab34a258e9a251980cdcdc0a120f6a` |
| B3 | `stage-3/sync-progression-schema-47-52` | [#376](https://github.com/zidaneyoung/Achiwave/pull/376) | `702f127198f0e31c8aaf2eca789b8f0fb66483e8` |
| B4 | `stage-3/achievement-schema-53-56` | [#377](https://github.com/zidaneyoung/Achiwave/pull/377) | `1ca63f8e7d3ae25cff3f3b947ef70577ae0946b4` |
| B5 | `stage-3/notification-evidence-schema-57-61` | [#378](https://github.com/zidaneyoung/Achiwave/pull/378) | `ca867aa9588db62a642ab289f01890f4112261db` |
| B6 | `stage-3/integrity-migration-tests-62-64` | Pending publication; replace with the actual PR before merge | Pending |

## Issue traceability

The command keys in the final column expand to the exact commands and results in
the verification section. `PG` includes clean migrations, representative valid
inserts, and named PostgreSQL constraint failures. `FULL` includes all Stage 2
regression tests.

| Issue | Branch | Commit SHA | Revision | Models and primary files | Principal integrity evidence | Command / result | Status |
|---|---|---|---|---|---|---|---|
| #37 | B1 | `b8fe044` | `20260731_0037` | `models/user.py`; `0037_users.py` | canonical identity uniqueness, normalized shape, positive versions | FULL + PG: pass | Pass |
| #38 | B1 | `1f70834` | `20260731_0038` | `models/user_preference.py`; `0038_user_preferences.py` | one row per user, named-zone shape, positive timezone version | FULL + PG: pass | Pass |
| #39 | B1 | `3956276` | `20260731_0039` | `models/registered_device.py`; `0039_registered_devices.py` | composite user ownership, active-installation partial uniqueness | FULL + PG: pass | Pass |
| #40 | B1 | `425e310` | `20260731_0040` | `models/device_session.py`; `0040_device_sessions.py` | device/user agreement, opaque digest, lifecycle checks | FULL + PG: pass | Pass |
| #41 | B1 | `bbd7b75` | `20260731_0041` | `models/push_token.py`; `0041_push_tokens.py` | token/device/user/platform/environment agreement, private representation | FULL + PG: pass | Pass |
| #42 | B2 | `0e08add` | `20260731_0042` | `models/campaign.py`; `0042_campaigns.py` | immutable ownership, explicit state and archive lifecycle | FULL + PG: pass | Pass |
| #43 | B2 | `09692fd` | `20260731_0043` | `models/quest.py`; `0043_quests.py` | campaign/user ownership, nonnegative XP, typed quest/state values | FULL + PG: pass | Pass |
| #44 | B2 | `e517d74` | `20260731_0044` | `models/quest_recurrence.py`; `0044_quest_recurrences.py` | one recurrence, frequency-field grammar, dates and named zone | FULL + PG: pass | Pass |
| #45 | B2 | `0e2a7b4` | `20260731_0045` | `models/quest_occurrence.py`; `0045_quest_occurrences.py` | ownership snapshot, one-time/recurring partial uniqueness | FULL + PG: pass | Pass |
| #46 | B2 | `3498a0f` | `20260731_0046` | `models/quest_completion.py`; `0046_quest_completions.py` | active-completion uniqueness, immutable reversal and ownership chain | FULL + PG: pass | Pass |
| #47 | B3 | `4821703` | `20260731_0047` | `models/client_mutation.py`; `0047_client_mutations.py` | one user/mutation binding, payload hash and target binding | FULL + PG: pass | Pass |
| #48 | B3 | `3bafc1a`, `a75dba2` | `20260731_0048` | `models/synchronization_operation.py`; `0048_synchronization_operations.py` | device/mutation ownership, attempt and terminal-state consistency | FULL + PG: pass | Pass |
| #49 | B3 | `f52e39b`, `7921a1d` | `20260731_0049` | `models/progress_event.py`; `0049_progress_events.py` | unique ordered per-user sequence without duplicate index | FULL + PG: pass | Pass |
| #50 | B3 | `bae3ffa`, `685d883` | `20260731_0050` | `models/xp_ledger_entry.py`; `0050_xp_ledger_entries.py` | one award/reversal source, reason/delta checks, linked compensation | FULL + PG: pass | Pass |
| #51 | B3 | `cfddf6f` | `20260731_0051` | `models/level_definition.py`; `0051_level_definitions.py` | positive level, nonnegative and unique curve thresholds | FULL + PG: pass | Pass |
| #52 | B3 | `21cfc0e`, `6797b86` | `20260731_0052` | `models/streak.py`; `0052_streaks.py` | one user/day credit, source and reversal ownership | FULL + PG: pass | Pass |
| #53 | B4 | `d5c67db`, `d804c77` | `20260731_0053` | `models/achievement_definition.py`; `0053_achievement_definitions.py` | stable key/version, PostgreSQL-safe key checks, visibility policy | FULL + PG: pass | Pass |
| #54 | B4 | `687c1e7`, `375b2a9` | `20260731_0054` | `models/achievement_rule.py`; `0054_achievement_rules.py` | one structured private rule per definition version; no public repr leak | FULL + PG: pass | Pass |
| #55 | B4 | `7bc9b1f` | `20260731_0055` | `models/achievement_progress.py`; `0055_achievement_progress.py` | unique backend-derived progress and source-event ownership | FULL + PG: pass | Pass |
| #56 | B4 | `b880e56` | `20260731_0056` | `models/achievement_unlock.py`; `0056_achievement_unlocks.py` | immutable one-time unlock per user/definition/version | FULL + PG: pass | Pass |
| #57 | B5 | `106482d` | `20260731_0057` | `models/notification.py`; `0057_notifications.py` | user ownership, privacy/content modes, presentation lifecycle | FULL + PG: pass | Pass |
| #58 | B5 | `7d166f9`, `67702ae` | `20260731_0058` | `models/notification_delivery.py`; `0058_notification_deliveries.py` | notification/device/token/outbox ownership, positive attempt audit | FULL + PG: pass | Pass |
| #59 | B5 | `3c2740c` | `20260731_0059` | `models/reminder.py`; `0059_reminders.py` | quest/occurrence ownership, named-zone schedule and due indexes | FULL + PG: pass | Pass |
| #60 | B5 | `9bd4bb3`, `67702ae` | `20260731_0060` | `models/evidence_attachment.py`; `0060_evidence_attachments.py` | cross-user ancestry rejection, no file body, size/digest/storage checks | FULL + PG: pass | Pass |
| #61 | B5 | `90ff70a`, `67702ae` | `20260731_0061` | `models/outbox_event.py`; `0061_outbox_events.py` | payload guardrails, nonnegative attempts, due/stale polling indexes | FULL + PG: pass | Pass |
| #62 | B6 | `5865cd7` | `20260731_0062` | integrity audit migration plus six mapped models | six PostgreSQL-safe timezone checks; 17 justified FK indexes; no duplicate definitions | FULL + PG + ALEMBIC: pass | Pass |
| #63 | B6 | `99290d4` | N/A; behavior already encoded through `0062` | `test_migrations.py`; `stage-3-schema.md` | all 51 FKs explicit: 50 `RESTRICT`, one documented `CASCADE`; both paths tested | FULL + PG: pass | Pass |
| #64 | B6 | `ba6a79a` | N/A; tests target head `0062` | `test_stage3_postgres.py` | destructive-DB guard, lifecycle, table/metadata parity, valid chain, named failures | FULL + PG + ALEMBIC: pass | Pass |

## Schema inventory

Stage 3 adds 28 mapped PostgreSQL tables through revisions `0037`–`0061`, plus
the `0062` integrity audit. The model package contains users and preferences;
devices, sessions, and push tokens; campaigns, quests, recurrences, occurrences,
completions, and reversals; client mutations, synchronization operations,
progress events, XP ledger entries, level definitions, streak summaries/days/
sources; achievement definitions/rules/progress/unlocks; notifications,
delivery attempts, reminders, evidence metadata, and outbox events.

At head, PostgreSQL reports 28 Stage 3 tables, 29 named primary keys, 51 named
foreign keys, 48 named unique constraints, 192 named check constraints, and 148
indexes including constraint backing indexes. Of these, 119 are explicitly named
`ix_…` query-support indexes or `uq_…` unique/partial indexes. PostgreSQL 18 also
reports generated not-null constraints separately; those are not included in the
named check count.

## Verification evidence

Commands ran from `apps/backend` using its checked-in package configuration and
existing `.venv`. `$ACHIWAVE_TEST_DATABASE_URL` pointed only to the explicitly
disposable database `achiwave_stage3_b6`; the committed tests refuse destructive
execution unless the database name contains `test`, `stage3`, or `ci`.

### META — safe metadata path

```powershell
Remove-Item Env:ACHIWAVE_TEST_DATABASE_URL -ErrorAction SilentlyContinue
$env:PYTHONPATH = 'src'
python -m pytest tests/test_migrations.py tests/test_stage3_postgres.py -q
```

Actual result: `3 passed, 2 skipped in 1.32s`. The destructive PostgreSQL tests
skip when no explicit test-database URL exists.

### PG — repeatable PostgreSQL migration and integrity path

```powershell
$env:PYTHONPATH = 'src'
$env:ACHIWAVE_TEST_DATABASE_URL = '<explicit disposable PostgreSQL URL>'
python -m pytest tests/test_stage3_postgres.py -q
```

Actual result: `2 passed in 5.30s`. The suite reset the disposable database,
upgraded from base to head, downgraded to `20260731_0001`, re-upgraded to head,
inserted a complete representative dependency chain, verified named constraint
failures, verified protected deletion, and verified the preferences cascade.

### FULL — backend regression suite with PostgreSQL enabled

```powershell
$env:PYTHONPATH = 'src'
$env:ACHIWAVE_TEST_DATABASE_URL = '<explicit disposable PostgreSQL URL>'
python -m pytest -q
```

Actual result: `37 passed in 5.95s`. Existing FastAPI health, configuration,
logging, SQLAlchemy, Alembic, Redis/Celery, worker, scheduler, and readiness tests
remain passing alongside Stage 3 tests.

### ALEMBIC — revision and drift checks

```powershell
$env:ACHIWAVE_DATABASE_URL = '<explicit disposable PostgreSQL URL>'
python -m alembic heads
python -m alembic current
python -m alembic upgrade head
python -m alembic check
```

Actual result: one head and current revision `20260731_0062`; upgrade succeeded;
`No new upgrade operations detected.` The PG test separately proves the full
downgrade and re-upgrade path.

### COMPOSE — built stack and live readiness

```powershell
docker compose -p achiwave_stage3_verify -f infrastructure/compose.local.yaml up --build -d
docker compose -p achiwave_stage3_verify -f infrastructure/compose.local.yaml run --rm backend python -m alembic upgrade head
docker compose -p achiwave_stage3_verify -f infrastructure/compose.local.yaml ps
Invoke-RestMethod http://127.0.0.1:58000/health/live
Invoke-RestMethod http://127.0.0.1:58000/health/ready
```

Actual result: the isolated Compose project built successfully. PostgreSQL,
Redis, and backend reported healthy; worker and scheduler remained running. The
clean Compose database upgraded through `20260731_0062`. Liveness returned
`{"status":"ok"}` and readiness returned PostgreSQL and Redis as `ok`. The
isolated containers, network, and `achiwave_stage3_verify_postgres_data` test
volume were then removed with `down -v --remove-orphans`.

## Deletion, privacy, and application boundaries

Campaign and quest user-facing deletion remains archive/tombstone state. Device,
session, token, reminder, notification, evidence, completion, progression,
achievement, delivery, and outbox history cannot be erased through an ordinary
cascade. `user_preferences` is the sole safe dependent cascade. Permanent account
erasure still requires a future coordinated privacy workflow.

Database checks enforce stable shapes, ownership, state, uniqueness, numeric
bounds, and critical idempotency. Full IANA timezone-database validation,
append-only write permissions, event-sequence allocation, immutable ownership
updates, recurrence evaluation, reward transactions, payload allowlists, and
privacy erasure ordering require later backend services and database roles. No
Stage 4 authentication or application endpoint was added.

## Dependencies and limitations

No dependency was added. PostgreSQL integration uses the already-declared
`psycopg`, SQLAlchemy, Alembic, and pytest stack. GitHub has no configured Actions
checks for these pull requests, so the recorded local and PostgreSQL verification
is the available required-check evidence. The final audit repeats the clean
migration, backend suite, and readiness checks on merged `main`.
