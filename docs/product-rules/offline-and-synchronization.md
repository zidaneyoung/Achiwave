# Offline and multi-device synchronization

This document is normative for issues #13–#14.

## #13 — Offline completion and synchronization

### Supported offline boundary

Mobile may cache campaigns, quests, occurrences, confirmed progression, and
achievement presentation data for read-only display. MVP queues only occurrence
completion. Campaign/quest creation or edit, archive/restore, reversal, timezone
change, account operations, and progression mutations require an authenticated
online request.

Offline data is never authoritative. A queued completion is visibly `pending`; it
must not confirm XP, level, streak, campaign completion, or achievement unlock.

### Operation record and privacy

Each durable operation contains:

- local queue ID and UUID client mutation ID generated once per logical tap;
- authenticated account scope and registered device ID;
- operation type and occurrence target;
- expected occurrence version and canonical payload hash;
- device-observed time and saved timezone snapshot as metadata;
- queue schema version, attempt count, due/last-attempt times, state, safe error
  class, and server result IDs when known.

Access/refresh tokens, hidden achievement rules, private evidence, and unrestricted
server responses are not queue fields. Queue storage is encrypted or protected by
platform facilities, partitioned by account, and inaccessible to another account.
Logs may contain redacted mutation IDs but no tokens or private payload.

Backend uniqueness is `(user_id, client_mutation_id)`. Exact identifier/payload
replay returns the stored result. Identifier reuse with a different payload hash is
a permanent conflict. Reward-bearing uniqueness independently prevents two active
completions or awards for one occurrence.

### Offline operation lifecycle

| State | May transition to | Rule and user-visible state |
|---|---|---|
| `pending` | `in_flight`, `cancelled` | Durable and waiting; show pending. |
| `in_flight` | `succeeded`, `retryable_failure`, `permanent_failure`, `cancelled` on logout | Leased for one bounded submission. Stale lease after app termination returns to `pending`. |
| `retryable_failure` | `in_flight`, `cancelled` | Preserve operation and safe reason; show retrying or manual-retry option. |
| `succeeded` | none | Persist canonical server IDs/result before updating confirmed UI; remove payload under local retention policy. |
| `permanent_failure` | none | Stop automatic retry; show reason and rollback optimistic state. User may dismiss evidence but cannot resubmit same invalid mutation as a new logical action without reconciling. |
| `cancelled` | none | Never submit; remove private payload after minimal non-sensitive local audit. |

State must be explicit; nullable timestamps cannot substitute for it.

### Submission and retry policy

Mobile owns queue scheduling:

1. require an eligible authenticated session;
2. lease a bounded due batch and preserve per-occurrence order;
3. submit with stable mutation ID and expected version;
4. persist response classification and canonical result before confirmed UI;
5. refresh affected server state; and
6. stop on authentication failure until controlled reauthentication.

Retryable failures are timeout, network loss, temporary server/dependency
unavailability, and rate limiting. Permanent failures are invalid payload, ownership
failure, archived/deleted/expired target, invalid state, unsupported schema,
payload-mismatched mutation reuse, and unrecoverable stale conflict.

Automatic retry uses exponential backoff starting at 5 seconds, doubling to a
15-minute cap, with platform-safe jitter; a longer server `Retry-After` wins.
After 8 automatic attempts, operation remains `retryable_failure` for manual retry.
Manual retry performs one immediate attempt after authentication/network checks and
then resumes the bounded policy. Authentication failure pauses rather than
consuming ordinary retry attempts.

### Lifecycle, ordering, and rejection

- Duplicate taps reuse one local operation. If duplicates still reach backend,
  occurrence uniqueness returns one completion.
- Timeout after commit is retryable; replay returns the committed result.
- Operations for the same occurrence are serialized. Independent occurrences may
  use bounded concurrency.
- A server rejection is persisted before optimistic state rolls back so restart
  cannot resurrect pending UI.
- Archive or deletion processed before queued completion makes it a permanent
  failure. Client-observed earlier time does not override server order.
- A stale edit that does not alter a generated occurrence does not invalidate its
  completion; occurrence version, not mutable display fields, is decisive.
- Logout warns about pending work. If confirmed, all account queue operations are
  cancelled and private payloads, credentials, caches, temporary files, push-token
  association, notification history, and in-memory state are cleared. Account
  switching follows the same rule. Cancelled work is not restored on later login.
- Device/session revocation pauses submission immediately and clears protected local
  data when the client learns of revocation.

### Offline examples

- Rapid offline taps: one queue record, one UUID, one later completion and award.
- Server commits but response drops: retry returns `succeeded` with original IDs.
- Quest archived while phone offline: queued completion becomes permanent failure,
  pending checkmark rolls back, no reward.
- App restarts with `in_flight` lease expired: operation returns to `pending` with
  same mutation ID.
- User logs out with pending work: explicit warning; confirmed logout cancels and
  clears it, protecting the next account.

Queue implementation, storage technology, API endpoints, and background execution
belong to later stages.

## #14 — Multiple-device synchronization

### Device and version assumptions

Each installation later registers a revocable device record bound to authenticated
sessions and platform/environment. Device ID identifies synchronization and
presentation context; it is not proof of ownership. Push tokens are separate,
rotatable, private values and are never progression authority.

Mutable server resources expose monotonically increasing versions. Mobile submits
expected versions for edits, lifecycle commands, timezone updates, completion, and
reversal. Backend returns structured conflict code, current version, and only the
authenticated user's canonical state. Reward operations use domain uniqueness and
event ordering, never generic last-write-wins.

### Conflict matrix

| Conflict class | Winning rule / rejected operation | Resulting authoritative state | User-visible outcome |
|---|---|---|---|
| Same occurrence completed on two devices | First committing eligible completion wins. Same mutation replay returns it; different mutation returns `duplicate_completion` with canonical ID. | One active completion, one award, one derived progression update. | Both show completed after reconcile; loser gets no error implying lost work and no second reward. |
| Exact mutation replay | Stored `(user, mutation ID, payload hash)` result wins. | Original timestamps, IDs, and effects unchanged. | Retry becomes succeeded without duplicate animation. |
| Mutation ID reused for different payload | Existing binding wins; new payload permanently rejected. | Existing result unchanged. | Controlled conflict; client stops retrying and refreshes. |
| Edit versus completion | Generated occurrence snapshot isolates title/reward/schedule edits. Completion may succeed if occurrence version and eligibility remain current. If edit invalidates occurrence first, stale completion rejects. | Either edited definition plus unchanged occurrence completion, or invalidated occurrence without completion. | Refresh shows edited definition and canonical occurrence; rejected pending state rolls back. |
| Archive versus completion | Lower committed event sequence wins. Archive first blocks completion; completion first commits once and later archive retains it. Device-observed time cannot reorder. | Archived definition/campaign with zero or one pre-archive active completion. | Archive visible after refresh; rejected completion shows permanent failure, accepted one retains reward/history. |
| Reversal versus completion | Expected occurrence version and sequence win. Reversal of active completion increments version; a pre-reversal stale completion cannot reinstate it. Fresh post-reconcile recompletion may succeed if eligible. | Exactly one of active completion or reversed state after each ordered transaction. | Stale device refreshes; no oscillation or duplicate XP. |
| Two reversals | First valid reversal wins; other returns canonical already-reversed result. | One reversal and one compensation entry. | Both show reversed; one compensation presentation at most. |
| Two quest/campaign edits | First expected-version commit wins; second stale edit rejects. No field-level merge in MVP. | First complete server document. | Losing device preserves local draft for user comparison, refreshes canonical state, and may explicitly retry. |
| Two timezone updates | First current-version update wins; second stale update rejects. | One saved zone with ordered change history; old occurrences unchanged. | Losing device displays current zone and asks user to resubmit intentionally. |
| Achievement unlock evaluation | Unique unlock constraint and first satisfying event win. | One immutable unlock and one presentation event. | Atomic claim allows one full celebration; every device shows unlocked collection state. |
| Level/streak presentation on devices | Authoritative event ID plus atomic user-level presentation claim wins. | One progression state and one claimed full presentation event. | Other devices update values without replaying full celebration. |
| Stale device after deletion/archive | Current server tombstone/archive wins. | No unauthorized resurrection; retained history follows deletion rules. | Local item removed/marked archived; queued mutations fail permanently. |
| Logout, revocation, or device removal | Backend session/device status wins immediately. | Server data intact; device loses access and push association is deactivated. | Client stops sync, clears protected local data, and requires authentication. |

### Deterministic reconciliation

Every successful or conflict response includes affected authoritative records,
versions, stable event IDs, and safe reason codes. Mobile first persists queue
outcome, then replaces affected cached authority with server state. It may merge
only presentation-only fields that never affect progression.

Out-of-order arrival is handled by mutation identity, expected versions, source
relationships, and event sequence. Backend may process independent operations in
parallel, but their final constrained state must equal a valid serial order.

An offline or stale device never overwrites XP totals, level, streak, campaign
completion, achievement progress, unlocks, timestamps, or another device's accepted
completion. Reauthentication and full scoped refresh are required after missed
version history or revocation.
