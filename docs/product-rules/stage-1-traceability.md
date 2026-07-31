# Stage 1 issue traceability

Authoritative scope checked on 2026-07-30 against GitHub milestone
`Stage 1 - Product Rules and Domain Foundation` (milestone 1): 17 open issues,
issues #1–#17, with a linear dependency chain. Issue #18 is Stage 2 and excluded.

Verification result means the documentation contains a deterministic rule, owner,
boundary/exception behavior, implementable acceptance evidence, and representative
examples for the issue. Repository-level command evidence is recorded in the
[acceptance audit](../testing/stage-1-acceptance.md).

| Issue | Documentation file | Exact section | Acceptance evidence | Verification result |
|---:|---|---|---|---|
| #1 | [domain-model.md](domain-model.md) | `#1 — Campaigns as high-level personal objectives` | Formal aggregate/owner/properties, empty/mixed quest rules, derived completion, invalid/boundary examples. | **Pass** — complete and deterministic. |
| #2 | [domain-model.md](domain-model.md) | `#2 — Quests as campaign actions` | Exactly-one campaign, immutable owner/association, required/optional fields, eligibility/reward/schedule validation and examples. | **Pass** — complete and deterministic. |
| #3 | [domain-model.md](domain-model.md) | `#3 — One-time and recurring quests` | Occurrence identity, MVP grammar, end/skip/miss/edit/archive/timezone semantics, implementation deferral. | **Pass** — complete and deterministic. |
| #4 | [state-transitions.md](state-transitions.md) | `#4 — Quest states and transitions` | Complete definition/occurrence state inventory, transition actors, preconditions, side effects, replay and forbidden cases. | **Pass** — state audit complete. |
| #5 | [state-transitions.md](state-transitions.md) | `#5 — Campaign states and transitions` | Initial/derived/archive/restore transitions, quest effects, history, mobile/backend split, forbidden cases. | **Pass** — state audit complete. |
| #6 | [state-transitions.md](state-transitions.md) | `#6 — Completion and reversal behavior` | Eligibility, one active completion, duplicate/offline handling, authorized append-only reversal, compensation and concurrency. | **Pass** — duplicate/reversal audit complete. |
| #7 | [progression.md](progression.md) | `#7 — XP award and reversal` | Per-occurrence integer reward snapshot, backend ledger, exact-once constraints, negative compensation, nonnegative total, offline examples. | **Pass** — ledger invariants explicit. |
| #8 | [progression.md](progression.md) | `#8 — Level progression` | Versioned configurable threshold validation, exact boundaries, level-down, event/presentation dedupe across restart/devices. | **Pass** — no unsupported numeric curve invented. |
| #9 | [progression.md](progression.md) | `#9 — Streak calculation` | Global qualifying activity, effective dates, no grace, reversal/recalc, timezone/clock/offline rules, eight worked examples. | **Pass** — date and edge audit complete. |
| #10 | [progression.md](progression.md) | `#10 — Achievement progress and unlocks` | Backend models/evaluation, unique immutable unlock, reversal/retroactivity, offline and app-closed multi-device presentation. | **Pass** — unlock authority explicit. |
| #11 | [progression.md](progression.md) | `#11 — Visible and hidden achievements` | Visible/progress-hidden/secret response allowlists, post-unlock state, notification privacy, accessibility, client security. | **Pass** — concealment audit complete. |
| #12 | [time-and-timezone.md](time-and-timezone.md) | `#12 — User-local date and timezone behavior` | UTC/IANA source/precedence, date-only/DST/travel/change/offline/invalid-zone rules and prospective history safety. | **Pass** — timezone authority explicit. |
| #13 | [offline-and-synchronization.md](offline-and-synchronization.md) | `#13 — Offline completion and synchronization` | Supported boundary, durable record/state machine, stable IDs, retry classes/backoff, rollback, logout, ordering and examples. | **Pass** — queue policy complete; implementation deferred. |
| #14 | [offline-and-synchronization.md](offline-and-synchronization.md) | `#14 — Multiple-device synchronization` | Device/version assumptions and conflict matrix with winner, rejection, final state, and visible result for every required class. | **Pass** — conflict audit complete. |
| #15 | [history-and-deletion.md](history-and-deletion.md) | `#15 — Definitions and product boundary` | Archive/soft/permanent/account distinction, full effects matrix, restore/pending/audit/privacy/legal rules and examples. | **Pass** — history effects explicit. |
| #16 | [time-and-timezone.md](time-and-timezone.md) | `#16 — Authoritative timestamp behavior` | Timestamp definitions/responsibility matrix, client validation, skew/offline/reconnect/timezone/concurrent ordering examples. | **Pass** — timestamp matrix complete. |
| #17 | [mvp-boundary.md](mvp-boundary.md) | `#17 — In-scope product capabilities` | In/deferred capabilities, platforms, authority, offline/sync/progression/notification/evidence/security/web boundaries and Stage 2 gate. | **Pass** — MVP boundary definitive. |

## Dependency result

Each issue is documented after its dependency's concepts:

`#1 → #2 → #3 → #4 → #5 → #6 → #7 → #8 → #9 → #10 → #11 → #12 → #13 → #14 → #15 → #16 → #17`

No Stage 1 rule depends on Stage 2 implementation. Later implementers must carry
these contracts into API, database, worker, Android, iOS, and acceptance tests.
