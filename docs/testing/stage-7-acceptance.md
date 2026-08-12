# Stage 7 acceptance audit

Recorded 2026-08-12. Stage 7 covers issues #130 through #149. Final status is
`Pass` for the implementation and executable release gates. Physical-device-only
observations are individually `Unable to Verify`; they do not masquerade as
automated passes. Issue #150 remains open and no Stage 8 reward behavior is in
scope.

## Delivery traceability

| Issues | Branch | Pull request | Merge evidence |
| --- | --- | --- | --- |
| #130-#136 | `stage-7/completion-core-130-136` | [#397](https://github.com/zidaneyoung/Achiwave/pull/397) | merged as `9e7b3bd8440903ff70f1234ceffc7dc8f7114ff2` |
| #137-#138 | `stage-7/optimistic-feedback-137-138` | [#398](https://github.com/zidaneyoung/Achiwave/pull/398) | merged as `ae8049664f4699241d0014352041e221e3915251` |
| #139-#146 | `stage-7/offline-sync-139-146` | [#399](https://github.com/zidaneyoung/Achiwave/pull/399) | merged as `5f25d54c27193be0a3f55b3c6d32140a0528970e` |
| #147-#149 | `stage-7/multi-device-history-147-149` | [#400](https://github.com/zidaneyoung/Achiwave/pull/400) | linked PR is the authoritative merge record |

All implementation commits were made on those branches. The primary checkout
contained pre-existing user changes, so it was not switched or rewritten;
`origin/main` was fetched after each merge and every next clean worktree branch
was based directly on that updated remote tip. Merged implementation branches
were deleted locally and remotely when safe.

## Issue, commit, files, and status

| Issue | Commit SHA | Principal evidence files | Status |
| --- | --- | --- | --- |
| #130 | `d118a6dc0a94a17a0acacaa693dccb7d16c208d1` | `services/completions.py`, `api/completions.py`, `tests/completions/test_complete.py`, mobile completion API/screen | Pass |
| #131 | `9b61f41a54d734d40f0532b1ed6fcffc09dbca94` | completion service/schema/API, `test_reverse.py`, Android quest detail | Pass |
| #132 | `0a003aa95a33fb80cd56c5e3c106c5effd2a7b45` | completion schema/service, `test_timestamps.py`, mobile contracts | Pass |
| #133 | `77e9df8f4d648a104f8c84242ec43e0d3c523a1d` | completion service, `test_progress_events.py` | Pass |
| #134 | `b28e3aa8323b688b8dd94b7d08f9055e5a9da072` | migration `20260812_0084`, client-mutation model/service/tests | Pass |
| #135 | `bb56eb6b9cc33828b48090469f5ee9ff7b95af4e` | mobile submission registry/test and quest detail | Pass |
| #136 | `0ff2920c84e747791bdfabae70b0e8adec303531` | completion service, idempotency and PostgreSQL tests | Pass |
| #137 | `1f2b74247a313726d5fcbf821915691d83aef904` | mobile presentation store/test, protected-data purge | Pass |
| #138 | `06b6673ae87f11d88a923df09aef8e6c7297717f` | mobile failure classifier, presentation rollback, quest detail | Pass |
| #139 | `37162188aac3ab4fcb5bb8e4f47c76c5bf3b4bb0` | mobile queue policy/types/storage/service; Expo SQLite config | Pass |
| #140 | `d24f7aa74c079fba4420e8b4c3f6e0df27daed99` | SQLite migrations/storage, protected layout/profile/purge | Pass |
| #141 | `599bee47674cc26726f38022ca76238d16a69cb0` | sync engine/hook/tests, connectivity and protected layout | Pass |
| #142 | `f36e5c2e632f00564a0ae7a6f341835e04beb190` | scoped backend conflicts; mobile conflict parser/sync tests | Pass |
| #143 | `a57d24a1a6c9cb3631da3283e04bf74f86a5f0e8` | retry policy, queue/sync engine, deterministic clock/jitter tests | Pass |
| #144 | `c9f5ce0d2487572c3deb38cdec803d4f2044c012` | failure classification, terminal queue policy/storage tests | Pass |
| #145 | `569292e33190107cfee155bd616565dec20e15c3` | manual retry queue/sync API and Android controls | Pass |
| #146 | `0b479f39ee271f444e3ab43b8392181ff7d65f8e` | queue presentation model/test and accessible quest UI | Pass |
| #147 | `8f36fba75ff72287ca893234327ace7d1368fdc2` | two-device PostgreSQL race; monotonic mobile presentation; environment queue partition | Pass |
| #148 | `69e4079be3056cc701f7a9d75bd71e40b2102e21` | history API/schema/service and `test_completion_history.py` | Pass |
| #149 | `a23b8d59908f1f643f682a594b1a5faf0376c24a` | quest service recalculation, `test_progress_recalculation.py`, completed-campaign Android authoring | Pass |

PR #399 also contains review fix
`f0f4f334aac2ef972cff1f48d60c49d68ccf4fc3`, which makes synchronization
single-flight per account and prevents UI callback errors from downgrading a
persisted success.

## API routes

- `POST /api/v1/quest-occurrences/{occurrence_id}/complete`
- `POST /api/v1/quest-completions/{completion_id}/reverse`
- `GET /api/v1/quest-occurrences/{occurrence_id}/completion-history`
- Existing campaign/quest create, archive, restore, detail, list, and login/logout
  routes are exercised as regression and history boundaries.

## Migration and database constraints

Stage 7 adds migration `20260812_0084_link_client_mutation_devices.py`, revision
`20260812_0084`, after `20260808_0083`. It adds nullable historical device
context to client mutations, composite owner/device foreign key
`fk_client_mutations_device_user` with `ON DELETE RESTRICT`, and
`ix_client_mutations_device`.

Real PostgreSQL tests exercise the existing authoritative constraints:

- `uq_client_mutations_user_client_mutation`;
- `uq_quest_completions_active_occurrence` partial unique index;
- unique completion/reversal client mutation bindings;
- `uq_quest_completion_reversals_completion_id`;
- unique per-owner completion, reversal, and progress-event sequence numbers;
- owner/occurrence/campaign/device composite foreign keys; and
- restrictive history ancestry that prevents ordinary deletion.

No Stage 8 XP migration or ledger write was added. Completion, reversal,
multi-device, campaign, and history tests assert zero XP ledger rows.

## Executed verification

The database URL used below named the explicitly disposable database
`achiwave_stage7_test`; credentials are intentionally omitted from this record.

| Command | Actual result | Status |
| --- | --- | --- |
| `python -m pytest tests/completions/test_idempotency.py -q` | 5 passed, including two registered devices racing through independent PostgreSQL sessions | Pass |
| `python -m pytest tests/history/test_completion_history.py -q` | 2 passed: full current lifecycle plus paginated legacy rows with nullable device/mutation context and retained reversal reason | Pass |
| `python -m pytest tests/campaigns/test_progress_recalculation.py -q` | 3 passed: obligation transitions, empty campaign, finite and open-ended recurrence predicates | Pass |
| `python -m pytest tests/history tests/completions -q` | 22 passed | Pass |
| `python -m pytest tests/campaigns tests/quests tests/completions/test_progress_events.py tests/completions/test_reverse.py -q` | 62 passed | Pass |
| final post-review `python -m pytest -q` | 201 passed in 285.13 seconds; migration autogenerate reported no new operations | Pass |
| changed-file `python -m ruff check` | all selected Stage 7 backend files passed; repository-required FastAPI `B008` and existing timezone parse rule were excluded consistently | Pass |
| `python -m alembic heads` | one head: `20260812_0084` | Pass |
| `python -m alembic current` | `20260812_0084 (head)` | Pass |
| `python -m alembic check` | no new upgrade operations detected | Pass |
| `python -m alembic downgrade 20260808_0083` then `upgrade head` | downgrade and upgrade both completed on the disposable PostgreSQL database; current/check passed afterward | Pass |
| `npm ci` | 581 packages installed from lockfile; command succeeded | Pass |
| `npm run typecheck` | TypeScript completed with no errors | Pass |
| all existing mobile scripts (`test:navigation`, `platform`, `security`, `theme`, `components`, `feedback`, `accessibility`, `campaigns`, `quests`, `completions`) | 88 tests passed (9 + 2 + 1 + 8 + 1 + 1 + 2 + 8 + 23 + 33) | Pass |
| `npx expo-doctor` with documented development public environment | 20/20 checks passed | Pass |
| `npx expo export --platform android --output-dir <temporary G: path>` | 1,409 modules bundled; 30 files, 5,693,140 bytes | Pass |
| `git diff --check` and final diff inspection | no whitespace errors, credentials, databases, dependency directories, caches, or generated export output selected | Pass |

The first Expo invocation without public configuration stopped with the expected
configuration guard (`EXPO_PUBLIC_API_ENV` missing). It was rerun with the
documented non-secret development environment and passed Doctor/export. This is
recorded to distinguish an environment precondition from a code failure.

## Runtime and visual evidence

| Acceptance area | Evidence | Status |
| --- | --- | --- |
| Online completion/reversal, replay after commit, scheduled/expired/voided/archive/cross-user rejection, stale versions | FastAPI integration tests against PostgreSQL | Pass |
| One logical rapid-tap submission, optimistic pending/success/rollback, no reward presentation | deterministic mobile completion tests and typecheck | Pass |
| Queue schema, restart recovery policy, reconnection ordering, lease recovery, retry timing/jitter/cap/attempt limit/`Retry-After`, permanent stop, and manual retry | 33 completion tests with deterministic fakes | Pass |
| Account isolation, logout warning/purge, different-account sync runs | queue, auth, privacy, and sync-engine tests | Pass |
| Two registered devices converge; stale/delayed responses cannot regress newer state | real two-session PostgreSQL race plus monotonic presentation test | Pass |
| History preservation and campaign completion/reopen derivation | PostgreSQL lifecycle and predicate tests | Pass |
| Compact layout constants, large-text matrix, reduced motion, native-stack Android back metadata, keyboard resize, dialogs, labels, live regions, non-colour state, 48 dp targets | existing navigation/platform/theme/accessibility tests plus static review and Android export | Pass |
| Fresh install on physical storage, process-kill SQLite persistence, real network transitions, physical two-device race, Android back gesture, TalkBack reading order, physical touch targets | no physical device was available for this final gate | Unable to Verify |
| Local native APK rebuild | attempted during PR #399; native compilation could not finish within available disk/time, while Expo Doctor and Android export subsequently passed | Unable to Verify |

No screenshot or physical-device observation is claimed. Device-only items remain
release acceptance work; their absence does not alter the recorded automated and
PostgreSQL results.

## Boundary and final status

- Issues #130-#149 are represented by their required commits and four pull
  requests.
- Issue #150 is open and unimplemented.
- No XP award (including zero-XP ledger entries), level, streak, achievement,
  recurrence worker, notification, evidence upload, or offline reversal was
  introduced.
- The original user working tree was preserved; all implementation and evidence
  work occurred in the clean `C:\\aw7` worktree.
- Overall Stage 7 implementation and executable verification: `Pass`.
- Physical-device-specific acceptance listed above: `Unable to Verify`.
