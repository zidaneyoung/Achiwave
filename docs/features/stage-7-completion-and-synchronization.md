# Stage 7 completion and synchronization

Stage 7 implements server-authoritative one-time occurrence completion,
reversal, optimistic Android feedback, and a controlled offline completion
queue. It also exposes append-oriented completion history and recalculates
campaign state when obligations change.

## Scope and authority boundary

The backend owns eligibility, ownership, accepted timestamps, mutation
identity, occurrence and campaign versions, per-user event order, duplicate
prevention, history, and campaign-state derivation. Mobile may present a
pending projection, but it cannot convert that projection into authoritative
progress.

Stage 7 creates no XP ledger entry and derives no XP total, level, streak, or
achievement. Issue #150 and all reward evaluation remain Stage 8 work. Quest
recurrence authoring, generation, recovery workers, notifications, evidence
uploads, and offline reversal are also deferred. Campaign recalculation can
correctly evaluate recurrence rows already described by the data model, but
Stage 7 does not expose or operate recurrence authoring.

## Completion eligibility

`POST /api/v1/quest-occurrences/{occurrence_id}/complete` accepts an action
only when all of the following are true:

- the access token and registered-device context are active and belong to the
  same account;
- the occurrence, quest, and campaign share that owner and immutable ancestry;
- the campaign and quest definition are active;
- the occurrence is `available` or an eligible `reversed` occurrence;
- the server clock is inside its availability window;
- the expected occurrence version is current; and
- no active completion already exists.

Device-observed time and timezone are optional metadata. They never decide
eligibility, event order, campaign state, or future rewards. The accepted
completion receives server receipt and processing timestamps, a server-derived
effective local date, and the next per-user event sequence.

## Reversal and history

`POST /api/v1/quest-completions/{completion_id}/reverse` accepts only the
owner's active completion at the expected occurrence version. Archive does not
block correction. A reversal appends a `quest_completion_reversals` row and a
`completion_reversed` progress event, marks the original completion inactive,
and preserves its stable identifiers and timestamps. Recompletion, when still
eligible, creates a new completion; it never rewrites the prior pair.

`GET /api/v1/quest-occurrences/{occurrence_id}/completion-history` returns a
bounded owner-history page in event order, each optional reversal, mutation and
device context, authoritative timestamps, and source progress-event references.
Legacy retained records may have null device/mutation context and older nonblank
reversal reasons; the read contract preserves those rows rather than hiding or
rewriting them. Pagination defaults to 50 records and is capped at 100.
Ordinary quest detail continues to return only `active_completion_id`, keeping
the default view uncluttered. Cross-account targets are concealed as not found.

## API contracts and safe results

| Route | Success outcomes | Controlled results |
| --- | --- | --- |
| `POST /api/v1/quest-occurrences/{occurrence_id}/complete` | `completed`, `duplicate_completion` | `occurrence_not_found`, `stale_occurrence_version`, `occurrence_not_eligible`, `client_mutation_conflict`, `campaign_structure_invalid` |
| `POST /api/v1/quest-completions/{completion_id}/reverse` | `reversed`, `already_reversed` | `completion_not_found`, `stale_occurrence_version`, `completion_not_active`, `client_mutation_conflict`, `campaign_structure_invalid` |
| `GET /api/v1/quest-occurrences/{occurrence_id}/completion-history` | ordered owner history | `occurrence_not_found` |

Validation and authentication use the repository's standard safe error
envelopes. A stale or ineligible mutation may include only its scoped current
occurrence, campaign, active-completion reference, recent stable event
references, and latest event sequence. Private queued payloads and unrelated
account state are never returned.

## Versions, event sequence, and mutation binding

Every completion and reversal supplies a stable `client_mutation_id` and an
expected occurrence version. The backend binds the identifier to the owner,
authenticated device, operation, target, and SHA-256 hash of the canonical
payload. An exact replay returns the stored materialized result, including the
same IDs and timestamps. Reuse for another target, operation, or payload returns
`client_mutation_conflict` and creates no effect.

Accepted transitions increment the occurrence version. Campaign versions
increment only when their authoritative state changes or an obligation changes.
Completion/reversal and campaign transition events draw from one user-locked
event sequence. This produces deterministic order across registered devices.

PostgreSQL is the final duplicate barrier:

- `(user_id, client_mutation_id)` is unique for mutation bindings;
- one partial unique index permits only one unreversed completion per occurrence;
- completion and reversal mutation IDs are uniquely bound per owner;
- one reversal is allowed per completion;
- completion, reversal, and progress-event sequence numbers are unique per
  owner; and
- composite owner/occurrence/device relationships use restrictive foreign keys.

Migration `20260812_0084` adds authenticated device context to client mutations
with a composite `ON DELETE RESTRICT` foreign key and lookup index. The
completion/history constraints were provisioned by the existing Stage 3 chain
and are exercised again by Stage 7 PostgreSQL tests.

## Optimistic Android presentation

An eligible tap creates one in-memory pending overlay while preserving a
separate canonical snapshot. A keyed single-flight registry makes rapid taps
and rerenders share the same logical request and mutation identifier. Success
stores the canonical result before showing `synchronized`. A permanent
rejection records failure before rolling back to refreshed server state.

Canonical application is monotonic: an incoming response or refetch with a
lower occurrence version, campaign version, or known event sequence cannot
replace a newer presentation. A discarded delayed result triggers a scoped
refresh. No optimistic surface contains or suggests confirmed XP or rewards.

## Offline queue record and storage

Only `complete_occurrence` is queueable. Reversal, campaign/quest authoring,
archive, restore, and every reward-bearing Stage 8 operation require an online
server decision.

Queue schema version 1 stores:

- queue, account, registered-device, occurrence, and client-mutation IDs;
- operation type, expected occurrence version, and canonical payload hash;
- device-observed time and timezone metadata;
- explicit state, total and automatic attempt counts, next/last attempt time,
  and lease expiry;
- safe error class/message;
- canonical completion, campaign, event-sequence, and result snapshot fields;
  and
- creation, update, and terminal timestamps.

Tokens are never queued. Expo SQLite is app-private, uses WAL, foreign keys,
and secure deletion, and has an environment-specific database name. Every row,
query, listener, uniqueness rule, and synchronization run is account-scoped.
This partitions development/test/production storage first and accounts within
each environment second. The database persists across ordinary process death
and application restart.

States are `pending`, `in_flight`, `retryable_failure`, `succeeded`,
`permanent_failure`, and `cancelled`. In-flight work uses a lease so only an
expired lease can be recovered after interruption. Terminal evidence is
retained for seven days and then pruned.

## Reconnection, ordering, and retry

Network reachability, authenticated layout startup, foreground transitions,
and manual retry can start synchronization. Runs are single-flight per account,
not globally, and process that account's operations in stable creation order.
The queue persists the server result before the UI callback, preventing a
presentation failure from downgrading a committed success.

Recoverable network/server failures retry after 5 seconds, then exponential
delays with up to 20 percent positive jitter, capped at 15 minutes. A longer
valid `Retry-After` wins. Automatic scheduling stops at 8 attempts. Manual retry
is offered only for `retryable_failure`, uses the original mutation identity,
and never converts a permanent result into a retryable one.

Authentication loss, not-found ownership concealment, malformed or reused
mutation identity, stale version, archive, expiry, ineligibility, and unsupported
queue schema are permanent. These stop automatic retry, roll back optimistic
presentation, and refresh scoped canonical state where authentication permits.

## Multi-device conflict resolution

The server serializes owner progression using the user row and locks the target
occurrence and campaign. Two registered devices racing one occurrence converge
to one completion, one canonical completion event, and at most one campaign
transition. The losing logical request receives `duplicate_completion` with
the winner's IDs, versions, timestamps, and sequence.

Stale expected versions never invoke last-write-wins. Responses include enough
scoped canonical state to reconcile, followed by a quest refresh when needed.
Exact delayed replay returns its historical materialized response, while mobile
version/sequence guards prevent it from regressing newer cached state. Missed
history, revoked devices, and ended sessions cross the normal authenticated
refresh or full reauthentication boundary.

## Logout and protected-data purge

Logout detects nonterminal queued work and offers the user a chance to cancel
logout. If logout proceeds, authentication locks immediately, pending operations
are cancelled, canonical queued payloads are cleared, the environment queue
database is deleted, presentation/campaign caches are purged, and listeners are
notified. Account switching cannot expose another account's cache or queue.
Ordinary archive and restore preserve server history; only the later legal
account-deletion workflow may erase or de-identify it.

## Campaign-state recalculation

The backend recalculates an affected non-archived campaign in the same
transaction after completion, reversal, eligible recompletion, new quest
creation, quest archive, and quest restore. Campaign restore also derives its
state from retained obligations.

The predicate is:

- no qualifying obligations means `active`, never completed;
- every active one-time occurrence must be completed;
- a finite recurring quest must reach its end condition and have every
  generated non-voided occurrence completed; and
- an active open-ended recurring quest keeps the campaign active.

State changes increment the campaign version, use a server timestamp, and append
one `campaign_completed` or `campaign_reopened` event. Reversal of the last
required completion, a new unfinished obligation, or restoration of one reopens
the campaign. Archiving the final obligation leaves an empty active campaign.
Exact replay returns its prior snapshot without another transition event.

## Accessibility and responsive behavior

Pending, in-flight, synchronized, retryable, and permanent states use distinct
text, icons/status labels, live-region announcements, and actions rather than
colour alone. Buttons use the shared 48 dp target baseline. Existing compact
viewport, large-text, keyboard-resize, native Android back, dialog focus, and
reduced-motion foundations remain in force. Physical TalkBack, touch, process
death, and network-transition behavior require device acceptance in addition to
the deterministic tests and Android bundle export.
