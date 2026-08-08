# Stage 6 acceptance audit

## Result

Stage 6 implementation is complete through issue #129. Branch-wide local
acceptance is **Pass**, with device-only behavior separately marked **Unable to
Verify**. The final branch is in [pull request #393](https://github.com/zidaneyoung/Achiwave/pull/393)
and is awaiting merge. Issue #130
and all Stage 7 completion, XP-award, progression, recurrence-worker,
notification, and offline-mutation behavior remain out of scope.

## Traceability

| Issues | Branch | Commits | Pull request / merge | Status |
| --- | --- | --- | --- | --- |
| #108-#113 | `stage-6/campaign-management-108-113` | `26990fb`, `af97617`, `ee2a718`, `240bb9b`, `ff3b4e6`, `da7728c` | [#390](https://github.com/zidaneyoung/Achiwave/pull/390), merged as `c32ee098089d8317fb0fc79b04b4c95f20c7e3ce` | Pass; issues closed |
| #114-#118 | `stage-6/quest-authoring-114-118` | `077ab51`, `adad3f6`, `75fc7df`, `1c502b8`, `2c74811` | [#391](https://github.com/zidaneyoung/Achiwave/pull/391), merged as `f2658ec771b9e2670d3aed6409c73c8180f625e8` | Pass; issues closed |
| #119-#123 | `stage-6/quest-planning-119-123` | `6a1b69f`, `fa3a437`, `7f937c5`, `47a7012`, `1ca6c0b`, `189cfa8`, `46216d4` | [#392](https://github.com/zidaneyoung/Achiwave/pull/392), merged as `89ce156e38ea11f6be77d6db90670b683d758e7c` | Pass; issues closed |
| #124 | `stage-6/quest-discovery-integrity-124-129` | `d321f69` | [#393](https://github.com/zidaneyoung/Achiwave/pull/393) | Pass locally |
| #125 | `stage-6/quest-discovery-integrity-124-129` | `2b21706`, `56edd3d` | [#393](https://github.com/zidaneyoung/Achiwave/pull/393) | Pass locally |
| #126 | `stage-6/quest-discovery-integrity-124-129` | `c5d6798` | [#393](https://github.com/zidaneyoung/Achiwave/pull/393) | Pass locally; device interaction Unable to Verify |
| #127 | `stage-6/quest-discovery-integrity-124-129` | `32c4e86`, `56edd3d` | [#393](https://github.com/zidaneyoung/Achiwave/pull/393) | Pass locally; device interaction Unable to Verify |
| #128 | `stage-6/quest-discovery-integrity-124-129` | `9ee0dcf` | [#393](https://github.com/zidaneyoung/Achiwave/pull/393) | Pass locally; device interaction Unable to Verify |
| Lifecycle replay review fix | `stage-6/quest-discovery-integrity-124-129` | `3f91a03` | [#393](https://github.com/zidaneyoung/Achiwave/pull/393) | Pass locally |
| #129 | `stage-6/quest-discovery-integrity-124-129` | `52a4fb9` | [#393](https://github.com/zidaneyoung/Achiwave/pull/393) | Pass locally |

Review-fix commits on the first two branches were `ff0913f`, `c125f12`, and
`23bcbce`. The third branch used `fa3a437` for preference-fallback isolation and
`46216d4` for durable reorder replay and legacy fallbacks. Final-branch review
fixes are `3f91a03` (durable lifecycle response snapshots) and `56edd3d`
(loaded-window refresh and pending-form navigation). No implementation commit
was made directly on `main`.

## Issue artifact map

| Issue | Principal implementation and tests | API / migration |
| --- | --- | --- |
| #108 | `api/schemas/services/campaigns.py`, `tests/campaigns/test_create.py`, mobile Campaigns tab and `campaigns/new.tsx` | `POST /api/v1/campaigns`; existing Stage 3 schema |
| #109 | Campaign list service/schema/tests, mobile owner-keyed cache and active/archived tab | `GET /api/v1/campaigns`; no migration |
| #110 | Campaign detail service/schema/tests and `campaigns/[campaignId].tsx` | `GET /api/v1/campaigns/{id}`; no migration |
| #111 | Versioned campaign update service/conflict tests and edit screen | `PATCH /api/v1/campaigns/{id}`; no migration |
| #112 | Campaign archive service/replay tests and detail action | `POST /api/v1/campaigns/{id}/archive`; no migration |
| #113 | Campaign restore/re-derivation tests and detail action | `POST /api/v1/campaigns/{id}/restore`; no migration |
| #114 | `api/schemas/services/quests.py`, one-time creation/occurrence tests, mobile quest form | `POST /api/v1/campaigns/{id}/quests`; existing Stage 3 schema |
| #115 | Versioned immutable-snapshot update tests and quest edit/detail screens | `PATCH /api/v1/quests/{id}`; no migration |
| #116 | Quest lifecycle/replay tests and quest detail action | `POST /api/v1/quests/{id}/archive` and `/restore`; no migration |
| #117 | Owner/campaign immutability enforcement and `test_assignment.py` | Creation/detail contracts; no move route or migration |
| #118 | Quest description schema/service/form coverage | Existing `quests.description`; no duplicate migration |
| #119 | Due-date resolution/service/contracts/tests and mobile formatting | Existing due/timezone columns; no duplicate migration |
| #120 | Central quest configuration, category contracts/selectors/tests | `20260808_0080_add_quest_categories.py` |
| #121 | Central difficulty contracts/selectors/tests | `20260808_0081_add_quest_difficulty.py` |
| #122 | Backend-owned `0`, `10`, `20` configuration and reward tests/forms | `GET /api/v1/quests/authoring-options`; no migration |
| #123 | Transactional reorder service/tests and accessible move controls | `PUT /api/v1/campaigns/{id}/quests/order`; `20260808_0082_store_client_mutation_results.py` from review |
| #124 | Owner-scoped list service/tests and `quests/index.tsx`, `QuestListFilters.tsx` | `GET /api/v1/quests`; `20260808_0083_add_quest_filter_indexes.py` |
| #125 | Four `RefreshControl` surfaces and `refresh/singleFlight.ts` tests | Canonical existing reads; no backend or migration change |
| #126 | `QuestDueDateTimeField.tsx`, due-date helper/tests | `@react-native-community/datetimepicker` `9.1.0`; no backend change |
| #127 | Semantic form snapshots, `useDirtyFormGuard`, four guarded forms and tests | Mobile navigation only; no persisted drafts |
| #128 | Named archive copy, busy AppDialog behavior, campaign/quest detail dialogs | Existing archive APIs; no restore/delete change |
| #129 | `tests/history/test_archival_integrity.py` plus durable replay serializers/tests | Existing `0082` JSONB response field and unchanged PostgreSQL `RESTRICT` constraints |

The only Stage 6 native dependency added was the Expo-compatible Android date
and time picker at the version selected by `npx expo install`. No dependency was
added for filtering, refresh, form guarding, dialogs, or historical tests.

## Verification command map

Commands below are the commands actually executed, from the repository root for
paths beginning with `apps/` and otherwise from the named application directory.
Shared mobile checks were `npm run typecheck`, `npx expo-doctor`, and
`npx expo export --platform android`; all passed for each published branch and
again on the final branch.

| Issues | Targeted commands and actual result |
| --- | --- |
| #108-#113 | `python -m pytest apps/backend/tests/campaigns -q` -> 17 passed; `python -m pytest apps/backend/tests -q` -> 138 passed; every available mobile test script passed |
| #114-#118 | `python -m pytest apps/backend/tests/campaigns apps/backend/tests/quests -q` -> 31 passed; `python -m pytest apps/backend/tests -q` -> 152 passed; every available mobile test script passed |
| #119-#123 | `python -m pytest -q` -> 169 passed; `python -m pytest tests/test_stage3_postgres.py tests/test_migrations.py tests/quests -q` -> 36 passed after review fixes; every available mobile test script -> 36 passed |
| #124 | `python -m pytest tests/quests/test_list.py -q` -> 3 passed; `python -m pytest tests/test_migrations.py -q` -> 3 passed; Alembic heads/current/upgrade/check and the disposable downgrade/upgrade cycle passed |
| #125 | `node --experimental-strip-types --test src/refresh/singleFlight.test.mjs` -> 2 passed; `npm run test:campaigns` -> 8 passed; `npm run test:quests` -> 23 passed |
| #126 | `npm run test:quests` -> 23 passed; TypeScript and Android export passed; native dialog interaction Unable to Verify |
| #127 | `npm run test:navigation` -> 9 passed; `npm run test:campaigns` -> 8 passed; `npm run test:quests` -> 23 passed; TypeScript passed |
| #128 | `npm run test:components` -> 1 passed; `npm run test:campaigns` -> 8 passed; `npm run test:quests` -> 23 passed; TypeScript passed |
| #129 | `python -m pytest tests/campaigns/test_archive.py tests/campaigns/test_restore.py tests/quests/test_archive.py -q` -> 13 passed; `python -m pytest tests/history/test_archival_integrity.py -q` -> 1 passed |

The final backend coverage shards were also executed explicitly as
`python -m pytest tests/account tests/auth tests/devices tests/preferences
tests/profile tests/security -q` (82 passed), `python -m pytest tests/campaigns
-q` (19 passed), `python -m pytest tests/quests tests/history -q` (37 passed),
and `python -m pytest test_config.py test_database.py test_health.py
test_logging.py test_main.py test_migrations.py test_redis_client.py
test_scheduler.py test_stage3_postgres.py test_worker.py -q` (39 passed).
Together they cover every collected backend test exactly once.

## Accepted quest-authoring contract

The earlier contract gap is resolved in
[`quest-authoring.md`](../product-rules/quest-authoring.md):

- category is optional; `null` means Uncategorized, with exact lowercase
  machine values `personal`, `health`, `learning`, `work`, and `finance` and
  corresponding capitalized display labels;
- difficulty uses exact lowercase machine values `easy`, `medium`, and `hard`
  with capitalized display labels, remains independent from XP, and is required
  for new quests while legacy null rows remain readable;
- new or changed rewards use `0`, `10`, or `20` XP, while legacy configured and
  snapshotted rewards remain readable and are never rewritten; and
- active quest order is an owner-scoped, versioned, replay-safe presentation
  mutation over the complete active set, with archived quests excluded.

The backend exposes the accepted choices to authenticated mobile clients. The
database checks category and difficulty machine values but deliberately retains
only the established nonnegative XP constraint so unknown deployed legacy
rewards cannot be invalidated.

## Verification evidence through #123

Evidence was collected on 2026-08-08 against disposable PostgreSQL 18.4 on host
port 55436 and the clean Stage 6 worktree.

### Backend and migrations

- Pass: full backend regression suite, `169 passed` after the review fixes.
- Pass: Alembic has one head and current revision, `20260808_0082`.
- Pass: `alembic upgrade head` and `alembic check`; no new upgrade operations.
- Pass: real-PostgreSQL tests cover strict category and difficulty values,
  optional/legacy null behavior, all allowed and disallowed reward cases,
  immutable occurrence snapshots, lifecycle preservation, exact reorder sets,
  stale and concurrent writes, replay safety, and canonical contiguous order.
- Pass: review regression persists the original reorder response and returns it
  unchanged after a later reorder and campaign archive; the focused PostgreSQL,
  migration-chain, and quest suite passed `36 tests`.
- Pass: authoring and reordering create no XP ledger or progression side effect.

### Mobile

- Pass: all repository mobile scripts, `36 tests` total.
- Pass: TypeScript `tsc --noEmit`.
- Pass: Expo Doctor, `20/20` checks.
- Pass: Android export, `1,323 modules`.
- Pass: category, difficulty, and XP choices use accessible Stage 5 selectors;
  active quest ordering has visible move-up/down controls with 48 dp touch-target
  infrastructure, disabled boundary/ambiguous states, and screen-reader
  announcements. No drag or animation is required.
- Pass: review fixes keep authoritative due-date metadata visible with the
  `system` date-format fallback when preferences are unavailable and preserve
  authoring-options request errors; focused campaign and quest suites passed
  `17 tests`, and TypeScript still passed.

The Expo checks used the documented non-secret development public environment
values. Generated export artifacts were removed after verification.

## Final branch-wide verification

### Backend and PostgreSQL

- Pass: complete test coverage was run as four disjoint shards after the single
  monolithic `python -m pytest -q` process exceeded its 20-minute shell limit
  without producing a summary. The shards covered every collected backend test
  exactly once: account/auth/device/preference/profile/security `82 passed in
  300.85s`; campaigns `19 passed in 108.47s`; quests/history `37 passed in
  166.97s`; and all ten top-level test files `39 passed in 58.39s`. Aggregate:
  `177 passed` in `634.68s` of pytest time.
- Unable to Verify: the monolithic command itself timed out after `1204.1s` with
  no result. It was not retried on the branch; its coverage was replaced by the
  successful non-overlapping shards above.
- Pass: one Alembic head, `20260808_0083`; current at head; `upgrade head`
  completed; `alembic check` reported no new upgrade operations.
- Pass: disposable PostgreSQL downgrade/upgrade cycle
  `20260808_0083 -> 20260808_0082 -> 20260808_0083`, with final current at head.
- Pass: `compileall` over backend source, tests, and migrations.

### Mobile, Expo, and Android export

- Pass: a clean `npm ci --offline --ignore-scripts --no-audit --no-fund` installed
  the exact lockfile tree (`579 packages`); `npm ls --depth=0` was clean and the
  package/lock hashes were unchanged. An earlier ordinary `npm ci` attempt had
  timed out and left an incomplete tree; no result from that attempt is counted.
- Pass: every repository mobile test script, `55 passed` total: navigation 9,
  platform 2, security 1, theme 8, components 1, feedback 1, accessibility 2,
  campaigns 8, and quests 23.
- Pass: `npm run typecheck`.
- Pass: Expo Doctor, `20/20` checks.
- Pass: Android export, `1,351 modules`; the generated output contained 30 files
  (`5,473,527` bytes) and was moved out of the repository after inspection.
- Not applicable: the package defines no `lint` or generic `test` script, so
  neither command was invented.

### Infrastructure and repository hygiene

- Pass: `docker compose ... config --quiet`; the existing local Compose backend
  returned HTTP 200 for `/health/live` and `/health/ready`, with PostgreSQL and
  Redis both `ok`.
- Pass: committed and working diffs passed `git diff --check`; no tracked
  dependency directory, export, cache, `.env`, database, or SQLite artifact was
  found.

## Unable to Verify

This workstation exposes no Android SDK, ADB, Java, emulator, or physical-device
bridge. Emulator/physical-device navigation, TalkBack, keyboard/modal/back
behavior, device font scaling, physical touch targets, and rendered interaction
remain `Unable to Verify`; none are reported as passed from static or bundle
evidence.

## Verification evidence for #124-#129

- Pass: owner-scoped PostgreSQL quest-list coverage, `3 passed`, including
  pagination, deterministic ordering, all canonical statuses, archived-parent
  behavior, owner isolation, combined campaign/category/status/date filters,
  uncategorized values, validation, and saved-timezone inclusive boundaries.
- Pass: migration structure tests, `3 passed`; disposable PostgreSQL downgrade
  from `20260808_0083` to `20260808_0082` and upgrade back to head; `alembic
  current` reports `20260808_0083 (head)` and `alembic check` reports no new
  operations.
- Pass: quest/mobile contracts and Android picker helpers, `19 passed`;
  navigation `5 passed`; refresh single-flight `2 passed`; campaign `6 passed`;
  accessibility `2 passed`; TypeScript passed.
- Pass: semantic dirty-form snapshots and the single pending navigation guard
  are included in campaign `8 passed`, quest `21 passed`, and navigation
  `8 passed`; accessibility `2 passed`; TypeScript and diff checks passed.
- Pass: named archive-confirmation copy `2 passed`, components `1 passed`,
  campaign `8 passed`, quest `21 passed`, TypeScript, and diff checks. Pending
  archive requests lock both actions and Android dismissal; failures remain in
  the dialog and preserve the retry mutation identity.
- Pass: real-PostgreSQL lifecycle replay regression, `13 passed in 141.73s`.
  Campaign and quest archive/restore exact replays return their original
  materialized response after inverse transitions and an archived parent,
  without duplicate lifecycle events. Legacy SQL-NULL response rows retain an
  explicit current-state fallback rather than fabricated history.
- Pass: populated real-PostgreSQL historical-integrity graph, `1 passed in
  44.05s`. Campaign and quest archive/restore retained stable definitions and
  associations, occurrences, completion and reversal, XP award and exact
  compensation, progress events, removed streak source, achievement progress
  and unlock, and mutation/audit history. Default views hid archived content;
  owner historical views exposed it; cross-owner reads remained concealed;
  restore created no occurrence backfill; named quest and campaign `ON DELETE
  RESTRICT` constraints rejected physical deletion.
- Unable to Verify: native Android pull gestures, picker dialogs and Android back,
  TalkBack, physical touch targets, rendered viewport/font-scale behavior, and
  runtime scroll preservation because no Android runtime is available.

## Remaining acceptance work

No Stage 6 implementation or local verification issue remains. Pull-request
merge, issue closure, and the final `main` SHA are recorded in the completion
report after the final branch merges; a commit cannot contain its own future
merge SHA.
