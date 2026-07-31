# Time, timezone, and timestamp authority

This document is normative for issues #12 and #16.

## #12 — User-local date and timezone behavior

### Canonical model

- Store instants as UTC with sufficient precision to preserve server ordering.
- Store an IANA timezone identifier separately whenever local calendar behavior
  matters. Fixed offsets and abbreviations such as `AST` are not accepted timezone
  preferences.
- Backend owns the saved `user_timezone`, its version, `effective_at`, and change
  history.
- At account creation mobile may propose the current device IANA zone. Backend
  validates it. A missing or invalid proposal uses `UTC` and returns a promptable
  status; backend never guesses from IP address.
- Saved user preference wins over device timezone. Travel has no progression effect
  until the user explicitly submits a timezone update.
- Display formatting may use the saved preference and user locale. Display
  conversion never changes stored instants or progression facts.

Every timezone update requires the current user-record version. Backend validates
the IANA identifier, records old and new values with a server effective instant,
and applies the new zone only prospectively. Two-device conflicts follow normal
optimistic concurrency; a stale update is rejected.

### Date-only interpretation

A date-only quest or recurrence field denotes midnight-to-midnight calendar intent
in the quest's saved timezone, not UTC midnight and not the viewer device zone.
Start dates are inclusive. Inclusive end dates remain eligible through that local
date's valid end. One-time due instants should be stored as resolved instants plus
the timezone/context from which they were created.

Historical occurrences retain timezone and resolved-instant snapshots. A timezone
change:

- does not rebucket completed, expired, or already-generated occurrences;
- does not change existing completion effective dates;
- changes future, not-yet-generated recurrence dates;
- changes future one-time completion receipt-date conversion; and
- cannot create a second occurrence or reward for a local date already keyed.

Offline operations retain `device_observed_at` and timezone snapshot as metadata.
They target an existing server occurrence; their old timezone cannot override that
occurrence or current user preference.

### DST resolution

Recurrence is calculated in local calendar space before conversion to UTC.

- A scheduled local time that does not exist during a spring-forward gap resolves
  to the first valid instant after the gap.
- A scheduled local time that occurs twice during a fall-back overlap uses the
  earlier offset.
- Daily recurrence follows local dates, so UTC gaps may be 23 or 25 hours.
- A monthly day absent from a month is skipped.

These choices are stored on the generated occurrence and never recalculated after
completion.

### Manipulation and failure behavior

Changing device clock, offset, locale, or timezone can alter local presentation
only. It cannot create occurrences, select XP time, backdate one-time streak credit,
or unlock achievements.

If an installed timezone database later changes, existing occurrence snapshots
remain authoritative. New occurrences use the backend's then-active timezone data
version. If a previously saved zone becomes unavailable, backend preserves its
history, blocks schedule edits requiring calculation, uses `UTC` for new
unscheduled one-time receipt-date behavior, and requires selection of a new valid
zone. It never silently remaps the zone.

Examples:

- A Halifax daily quest at 09:00 remains tied to `America/Halifax` when the phone
  travels to Tokyo; only display may change until preference is updated.
- Updating to `Asia/Tokyo` after tomorrow's occurrence was generated leaves that
  occurrence unchanged and applies Tokyo to the next ungenerated date.
- A 02:30 recurrence on a spring-forward date resolves to the first valid instant;
  it does not disappear or generate twice.
- An invalid fixed-offset preference is rejected and the existing saved IANA zone
  remains.

## #16 — Authoritative timestamp behavior

### Timestamp meanings

| Value | Source | Authority and use |
|---|---|---|
| `server_received_at` | API edge/backend clock | Authoritative acceptance instant for online and replayed mutations; default progression time. |
| `server_processed_at` | Backend/worker clock | Audit and latency instant; not substituted for an earlier committed receive time. |
| `device_observed_at` | Mobile clock | Optional context only; never independently controls progression. |
| user-selected local date/time | User input | Scheduling intent only after backend validation; not proof an action occurred then. |
| `occurrence_local_date` | Backend recurrence calculation | Authoritative recurrence identity and recurring-completion streak date. |
| `completion_effective_date` | Backend rule | Recurring: occurrence local date. One-time: `server_received_at` in saved zone effective at receipt. |
| `created_at` | Backend clock | Authoritative record creation audit time. |
| `updated_at` | Backend clock | Latest accepted semantic change; cache invalidation, not event order by itself. |
| `archived_at` / `restored_at` | Backend accepted command | Authoritative lifecycle audit time and eligibility boundary. |
| `completed_at` | Backend | Completion `server_received_at`; reward/order audit. |
| `reversed_at` | Backend | Reversal `server_received_at`; compensation/order audit. |
| `unlocked_at` | Backend evaluation transaction | First authoritative satisfaction time; immutable. |
| `synchronized_at` | Backend and mobile separately | Server response/reconciliation audit; never rewrites source event time. |
| `event_sequence` | Backend transaction | Authoritative per-user order when timestamps tie or processing is concurrent. |

### Operation responsibility matrix

| Operation | Authoritative time / date | Context retained | Validation and edge behavior |
|---|---|---|---|
| Campaign/quest create or edit | `server_received_at`; backend `created_at`/`updated_at` | User schedule input and zone. | Stale versions reject; device time irrelevant. |
| Archive / restore | Command `server_received_at` plus event sequence. | Device-observed time optional. | Determines whether later received completion is eligible. |
| Occurrence generation | Backend-resolved scheduled instant and local date; generation processing time audited. | Rule and timezone-data version. | Deterministic key prevents duplicate scheduler runs. |
| Online completion | `server_received_at`; backend effective-date rule. | Device-observed time optional. | Current eligibility and version checked transactionally. |
| Offline completion | First authenticated server receipt of mutation; recurring effective date may use referenced occurrence date. | Original device observation and enqueue zone. | Late client time never reorders archive or expiry decisions. |
| Completion reversal | Reversal `server_received_at` and event sequence. | User reason, device observation. | Original completion time remains unchanged. |
| XP / level | Source event sequence and server times. | Rule/curve version. | Ledger and derivation follow authoritative source event. |
| Streak | Backend effective date set. | Historical timezone snapshots. | Reversal recalculates affected dates; old dates not rebucketed. |
| Achievement progress/unlock | Source event order; first satisfying backend evaluation transaction. | Rule version and source IDs. | Retry returns existing unlock. |
| Timezone update | Accepted update `server_received_at`. | Old/new zone and client proposal. | Prospective only; stale update rejected. |
| Synchronization | Server response time for audit; each source retains original authoritative time. | Mobile receipt and attempt times. | Reconnection cannot rewrite source times. |

### Client timestamp validation

When provided, device-observed timestamps must be ISO 8601 instants with an
explicit offset. Backend:

1. parses the value without using it for authorization or reward;
2. accepts it as metadata only when between `1970-01-01T00:00:00Z` and 24 hours
   after `server_received_at`;
3. otherwise stores an `invalid_or_implausible_client_time` audit flag and omits
   the raw value from normal product views; and
4. never rejects an otherwise valid completion solely because optional client time
   is absent or implausible.

This fixed bound prevents extreme values from corrupting storage while ensuring
clock skew cannot fabricate progression. Sensitive device metadata follows normal
account-deletion and log-minimization rules.

### Replays, reconnection, and concurrency

The first successfully authenticated receipt for a client mutation fixes its
`server_received_at`. Exact retries return that original time even if processed
later. A request that never reached the backend has no authoritative event time.

Backend assigns a per-user monotonic event sequence inside the committing
transaction. Domain order is event sequence, then stable event ID only for
diagnostic tie-breaking. Worker execution order and mobile upload order do not
override it.

Examples:

- Completion commits, response is lost, and retry arrives tomorrow: original
  completion and reward time remain.
- Archive sequence 40 commits before queued completion sequence 41: completion is
  rejected even if device says it occurred earlier.
- Two completions arrive at equal clock precision: unique constraints choose the
  active completion; event sequence gives a reproducible audit order.
- Timezone update commits after an occurrence was generated: occurrence keeps old
  snapshot; next ungenerated date uses the new zone.
