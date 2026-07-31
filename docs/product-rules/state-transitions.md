# State transitions, completion, and reversal

This document is normative for issues #4–#6. All transitions are accepted and
ordered by the backend. Mobile may request a transition or display a pending
projection, but may not persist authoritative state.

## Shared transition rules

- Every mutation is owner-scoped, uses a stable client mutation identifier where
  replay is possible, and is evaluated against current server state.
- A repeated mutation ID with the same canonical payload returns its original
  result and produces no new side effects. Reuse with a different payload is a
  permanent conflict.
- A distinct request that has already achieved the requested state returns the
  canonical state with an `already_applied` result and no side effects.
- Forbidden transitions return a controlled conflict, current record version, and
  authoritative state. They never partially award or erase progression.
- Accepted transitions increment record version and receive a per-user event
  sequence so concurrent events have one deterministic order.

## #4 — Quest states and transitions

### State model

Quest definition and occurrence use separate state machines:

| Object | State | Initial / terminal | Meaning |
|---|---|---|---|
| Definition | `active` | Initial, nonterminal | May expose eligible occurrences and, for recurrence, generate future occurrences. |
| Definition | `archived` | Nonterminal, reversible | Hidden by default; no generation or new completion. |
| Occurrence | `scheduled` | Initial for future, nonterminal | Exists but availability instant has not arrived. |
| Occurrence | `available` | Initial when immediately eligible, nonterminal | May accept one active completion. |
| Occurrence | `completed` | Nonterminal | Has one active completion and corresponding reward. |
| Occurrence | `reversed` | Nonterminal while eligible; otherwise effectively terminal | Prior completion was reversed; history remains and recompletion requires a fresh valid action. |
| Occurrence | `expired` | Terminal | Eligibility window ended without an active completion. |
| Occurrence | `voided` | Terminal | Server invalidated an uncompleted generated occurrence because its definition was invalidated; no reward. Ordinary archive does not void it. |

For a one-time quest, the product-visible quest state is definition archive first,
otherwise its sole occurrence state. For a recurring quest, product-visible state
is `archived` or `active`; each generated occurrence has its own state. A recurring
definition never transitions to `completed`.

### Definition transition table

| From → to | Initiator | Authority and preconditions | Side effects | Repeat behavior |
|---|---|---|---|---|
| creation → `active` | Owner through mobile/API | Backend validates owner, campaign active, type, schedule, and fields. | Creates one-time occurrence or establishes recurrence definition. | Same mutation returns created definition. |
| `active` → `archived` | Owner | Backend validates version. | Stops generation; blocks new completion; retains occurrence states and history; campaign state recalculates. | Returns existing archive event. |
| `archived` → `active` | Owner | Campaign is not archived; backend validates version and definition still valid. | Resumes generation from restore effective date without archived-period backfill; campaign recalculates. | Returns existing restore event. |

All other definition transitions are forbidden. There is no manual `completed`,
`deleted`, or client-only definition state. Permanent deletion is a privacy
workflow, not a lifecycle transition.

### Occurrence transition table

| From → to | Initiator | Authoritative system / preconditions | Side effects | Repeat behavior |
|---|---|---|---|---|
| generation → `scheduled` | Backend/worker | Deterministic key absent; availability is future. | Inserts snapshot; no progression. | Unique key returns existing occurrence. |
| generation → `available` | Backend/worker | Deterministic key absent; availability has arrived. | Inserts snapshot; no progression. | Unique key returns existing occurrence. |
| `scheduled` → `available` | Backend/worker | Server clock reaches resolved availability instant; definition/campaign active. | Makes occurrence eligible. | Already available returns current state. |
| `scheduled` → `voided` | Backend | Pre-completion administrative/domain invalidation; ordinary user archive is insufficient. | Audit event only. | Returns existing void event. |
| `available` → `completed` | Owner intent | Ownership, campaign/definition active, window open, expected version current, no active completion. | Completion, XP entry, campaign/streak/level/achievement evaluation, audit. | Same mutation returns result; duplicate logical completion returns canonical active completion without reward. |
| `available` → `expired` | Backend/worker | Eligibility window closed by server time. | No reward; campaign recalculates. | Already expired is unchanged. |
| `available` → `voided` | Backend | Domain invalidation before completion. | Audit event; no reward. | Already voided is unchanged. |
| `completed` → `reversed` | Owner in MVP | Active completion exists; target ID and expected version current. Archive does not block correction. | Reversal event, compensating XP entry, derived progression recalculation, campaign reopen if required. | Same mutation returns reversal; another reversal returns canonical reversed result. |
| `reversed` → `completed` | Owner intent | Occurrence still eligible, campaign/definition active, current version supplied, fresh mutation, no active completion. | New completion and reward events; old records remain. | Replay rules apply to new completion. |
| `reversed` → `expired` | Backend/worker | Eligibility window closes with no active completion. | No additional reward effect. | Already expired is unchanged. |

`expired` and `voided` have no outgoing transitions. An expired or voided
occurrence cannot be restored or completed. Correcting an erroneous server
invalidation requires an explicit administrative repair event designed in a later
stage, not a hidden state edit.

### Forbidden examples

- `scheduled → completed`: reject; future occurrence is not eligible.
- `completed → expired` or `completed → voided`: reject; reverse first if valid.
- `expired → completed`: reject even when device-observed time claims an earlier
  date.
- any occurrence transition while campaign or quest definition is archived, except
  `completed → reversed`: reject.
- mobile submits a state string without a domain command: reject.

## #5 — Campaign states and transitions

### States and derivation

| State | Initial / terminal | Meaning |
|---|---|---|
| `active` | Initial, nonterminal | Accepts quest creation and eligible quest activity. |
| `completed` | Derived, nonterminal | Current obligations satisfy the completion predicate in the domain model. |
| `archived` | Nonterminal, reversible | Hidden by default and blocks contained activity. |

`completed` is derived only. A client cannot manually complete or reopen a
campaign. `active` and `completed` are reconciled in the same authoritative
transaction, or immediately after it by an idempotent worker, whenever an
obligation changes.

### Transition table

| From → to | Initiator | Authority / preconditions | Effects on quests and history | Repeat behavior |
|---|---|---|---|---|
| creation → `active` | Owner | Backend validates owner and fields. | Empty campaign; no progression. | Same mutation returns created campaign. |
| `active` → `completed` | Backend derivation | At least one qualifying obligation and completion predicate true. | Quests unchanged; records campaign completion event and time. | Recalculation is idempotent. |
| `completed` → `active` | Backend derivation | Reversal, new quest, restored unfinished quest, or changed finite obligation makes predicate false. | Quests unchanged; records reopen reason and time. | Recalculation is idempotent. |
| `active` → `archived` | Owner | Current version; owner authorized. | Blocks quest creation, generation, and completion; existing occurrences/history retained. | Returns existing archive result. |
| `completed` → `archived` | Owner | Current version; owner authorized. | Same blocking behavior; completion history retained. | Returns existing archive result. |
| `archived` → `active` | Owner request plus backend derivation | Definition valid; current version. Predicate currently false. | Restores visibility and activity; no recurrence backfill. | Returns existing restore result. |
| `archived` → `completed` | Owner request plus backend derivation | Definition valid; current obligations still satisfy predicate. | Restores completed visibility; no duplicate completion reward. | Returns existing restore result. |

Archiving a campaign does not individually rewrite contained quest or occurrence
states. It supplies a higher-level eligibility block. Restoring recalculates the
campaign from retained quest state and resumes recurrence only from the restore
effective date.

Forbidden transitions include manual `active → completed`, manual
`completed → active`, `archived → archived` as a new event, and any client-written
state. State deletion is governed by the history and privacy document.

### Examples

- Completing the last finite occurrence derives `completed`.
- Reversing that occurrence derives `active` and compensates progression.
- Adding an unfinished quest to a completed campaign derives `active`.
- Archiving then restoring a still-satisfied campaign restores `completed` without
  awarding XP or creating another campaign-completion reward.
- A stale restore after another device archived the campaign again is rejected with
  current version and state.

## #6 — Completion and reversal behavior

### Completion invariant

An occurrence has at most one active completion. Completion acceptance requires:

1. authenticated owner matches campaign, quest, occurrence, and mutation scope;
2. campaign and quest definition are active;
3. occurrence is `available` or eligible `reversed`;
4. its server-defined window is open;
5. expected occurrence version is current;
6. mutation ID is new with a canonical payload or an exact replay; and
7. database uniqueness permits one active completion and one award source.

Acceptance persists the completion before or atomically with reward side effects.
If any part fails, none of completion, XP, level, streak, campaign, or achievement
state commits.

Rapid taps, timeouts after commit, automatic retries, and concurrent submissions
must resolve to one authoritative completion. Exact replay returns the original
status and IDs. A different mutation for an already-completed occurrence returns
the canonical completion with `duplicate_completion`; it creates no new reward.

Offline completion is `pending`, not complete, until the backend accepts it.
Rejection changes the local operation to permanent failure and rolls back any
optimistic checkmark; no confirmed reward animation is allowed.

### Reversal

Only the owner may request reversal of their active completion in MVP. A later
accepted support policy may add a role, reason requirements, and audit controls;
until then support actors are unauthorized. Possession of an ID alone is never
authorization. Reversal remains allowed after quest/campaign archive, recurrence
advancement, synchronization, or another device refresh because it is correction
of history, not new activity.

An accepted reversal:

- records immutable reason, actor, server timestamps, event sequence, and target;
- marks the completion inactive through a reversal relation rather than deletion;
- moves occurrence to `reversed`;
- appends the exact negative XP compensation;
- recalculates XP, level, affected streak interval, campaign state, and locked
  achievement progress;
- never relocks an already-unlocked achievement; and
- returns the full authoritative reconciliation snapshot.

If the occurrence remains eligible and active, a later fresh completion may move
it from `reversed` to `completed`. The old completion, reward, and reversal remain.
If its window has ended it cannot be recompleted.

### Concurrency and invalid cases

- Reversal after archive: accepted if target completion is active.
- Reversal after another device already reversed: canonical already-reversed result.
- Reversal racing a new completion: expected occurrence versions and event sequence
  establish order. A stale completion created before reversal cannot silently
  reinstate completion.
- Reversal of a different user's completion: not-found-style authorization failure
  with no ownership disclosure.
- Reversal of an expired/voided occurrence without active completion: conflict.
- Changing completion timestamps or deleting XP entries to simulate reversal:
  prohibited.

Completion, reward, reversal, and audit history are append-only except for
privacy-required erasure described in
[history, archival, and deletion](history-and-deletion.md).
