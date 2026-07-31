# Domain model and vocabulary

This document is normative for issues #1–#3.

## Shared glossary and data dictionary

| Term | Definition and invariant | Authority / identity |
|---|---|---|
| User | Authenticated owner of all private product records. Records never cross user boundaries. | Backend identity; stable `user_id`. |
| Campaign | User-owned high-level personal objective containing zero or more quests. | Backend; stable `campaign_id`, immutable owner. |
| Quest definition | User-owned action definition belonging to exactly one campaign. It describes type, reward, schedule, and future occurrence behavior. | Backend; stable `quest_id`, immutable owner and campaign. |
| One-time quest | Quest definition with exactly one occurrence. | `quest_type = one_time`. |
| Recurring quest | Quest definition whose schedule can produce at most one occurrence per user-local date. | `quest_type = recurring`; backend generation. |
| Occurrence | One eligible instance of a quest, including the sole instance of a one-time quest. Reward and schedule fields are snapshots. | Stable `occurrence_id`; unique `(quest_id, occurrence_local_date)` for recurring quests. |
| Completion | Accepted claim that one occurrence was completed. At most one non-reversed completion exists per occurrence. | Stable `completion_id`; backend accepted. |
| Client mutation | One logical mobile action submitted once or replayed with the same identifier and payload. | UUID generated once; unique per user on backend. |
| Reversal | Audited event that invalidates an active completion and compensates its derived rewards. It never erases the completion. | Stable `reversal_id`, references `completion_id`. |
| XP ledger entry | Immutable integer delta caused by one accepted completion or its reversal. | Stable ledger ID; unique source/reason relation. |
| Authoritative XP | Nonnegative sum of a user's ledger deltas. | Backend-derived. |
| Level curve | Versioned, ordered XP thresholds. | Backend configuration. |
| Streak day | User-local calendar date credited by server rules with at least one active qualifying completion. | Backend-derived effective date. |
| Achievement definition | Versioned backend rule with stable identifier, progress model, visibility, and unlock threshold. | Backend-only rule data. |
| Achievement unlock | Immutable first satisfaction of an achievement rule by a user. | Unique `(user_id, definition_id, rule_version)`. |
| Archive | Reversible product operation hiding a definition and blocking new activity without deleting history. | Server timestamp and version. |
| Soft deletion | Non-user-facing tombstone that hides a record while retaining references and audit data. | Backend/legal operation only in MVP. |
| Permanent deletion | Irreversible erasure or de-identification allowed only by account-deletion or legal workflow. | Privacy workflow. |
| Effective date | Local calendar date selected by backend rules for streak or recurrence semantics. | Never chosen by editable client state alone. |
| Record version | Monotonically increasing server value used to detect stale mutations. | Backend-assigned. |
| Event sequence | Per-user monotonic server order for concurrent authoritative events. | Backend-assigned transactionally. |

## Responsibility matrix

| Concern | Mobile client | Backend / worker / database |
|---|---|---|
| Identity and ownership | Supply authenticated session; isolate cached account data. | Authenticate and authorize every record access and mutation. |
| Campaign and quest input | Validate presence/shape for feedback. | Validate all rules, ownership, state, versions, and persistence. |
| Recurrence | Display server occurrences and future schedule preview. | Calculate and generate occurrences idempotently. |
| Completion | Queue or submit intent; show pending/failed/confirmed distinctly. | Accept or reject, deduplicate, timestamp, persist, and derive effects. |
| XP / level / streak | Present confirmed values; pending values cannot appear final. | Award, reverse, derive, reconcile, and audit. |
| Achievements | Render permitted state and claim a presentation event. | Keep rules, evaluate progress, unlock exactly once, conceal secrets. |
| Timezone | Propose a valid IANA identifier and format display time. | Validate preference, version changes, calculate effective dates. |
| Offline | Persist account-scoped completion mutations and retry safely. | Return deterministic idempotent results and authoritative snapshots. |
| Multi-device | Refresh on conflict and discard stale authority claims. | Version, order, constrain, resolve, and return canonical state. |
| Native behavior | Permissions, secure storage, haptics, audio, push handling. | Device/token registration and privacy-safe event delivery in later stages. |
| History / deletion | Hide archived items by default; clear private data on logout. | Retain or erase according to archival, audit, account, and legal rules. |

## #1 — Campaigns as high-level personal objectives

### Formal rule

A campaign is one user's durable objective and aggregation boundary for quests,
progress, and history. It is not a shared workspace, category, tag, reward, or
free-standing completion.

Required properties are stable ID, owner ID, nonblank title, lifecycle state,
record version, creation timestamp, and update timestamp. Optional properties are
description and display ordering. Display ordering has no progression effect.

Ownership is immutable. Every query and mutation is scoped to the authenticated
owner. Sharing, collaboration, transfer, and cross-account moves are not MVP
capabilities.

### Quest contribution and empty campaigns

- A campaign may exist with no quests so a user can plan an objective.
- Empty campaigns never derive `completed`.
- A campaign may contain one-time and recurring quests together.
- Every quest completion contributes through that quest's occurrence, reward, and
  campaign association; there is no separate client-calculated campaign score.
- A quest cannot be moved between campaigns. Archive it and create a new quest when
  the objective changes; history remains with its original campaign.

### Completion

Campaign completion is backend-derived, never a client toggle. A campaign becomes
`completed` only when it has at least one non-archived quest and:

1. every one-time occurrence is completed;
2. every finite recurring quest has reached its end condition and every generated,
   non-voided occurrence is completed; and
3. it has no active open-ended recurring quest.

Archiving a quest excludes it from future campaign obligations but retains its
history. Archiving the last obligation does not complete the campaign; it leaves
no qualifying obligations, so derived state is `active`. Reversal, restoration of
an unfinished quest, or creation of a new obligation reopens a completed campaign.
Manual completion is forbidden; manual archive is the supported way to stop an
unfinished objective.

### Examples and boundaries

- Valid: “Run a first 10K” with training quests; one campaign, one owner.
- Valid: an empty “Learn Spanish” campaign awaiting later quest creation.
- Valid: one campaign with “Buy textbook” once and “Practice daily” recurring.
- Invalid: a campaign owned by two users or a quest linked to two campaigns.
- Invalid: mobile sets campaign `completed` because its cache shows all quests done.
- Boundary: an open-ended daily quest keeps the campaign active until that quest is
  archived or edited to a finite schedule that finishes.
- Exception: account deletion can erase or de-identify campaign history under the
  privacy workflow; it is not a campaign state transition.

## #2 — Quests as campaign actions

### Formal rule and properties

A quest definition is a user-owned action that contributes to exactly one
campaign. Owner must equal campaign owner. Owner and campaign association are
immutable.

All quests require stable ID, owner ID, campaign ID, type, nonblank title,
nonnegative integer XP value, definition state, record version, and server creation
and update timestamps. Description, display order, availability start, due/end
condition, and recurrence fields are optional when compatible with the quest type.
Recurring quests additionally require a valid schedule, start local date, and IANA
schedule timezone.

Evidence is neither required nor accepted by the Stage 1 MVP rule. Later evidence
features may add an attachment policy without allowing a device to validate its own
completion.

### Completion and reward eligibility

- A completion targets an occurrence, not only a quest definition.
- The occurrence and campaign must belong to the authenticated user.
- Definition and campaign must not be archived when the backend receives the
  completion.
- Occurrence must be available, unexpired, non-voided, and have no active
  completion.
- Accepted completion creates one completion event and one XP ledger award,
  including a zero-value ledger entry when reward is zero for audit consistency.
- Quest reward is a nonnegative integer snapshot on the occurrence. Editing a quest
  reward affects only occurrences generated after the edit.
- Completion is explicit user intent. Merely opening, viewing, scheduling, or
  receiving a reminder never completes a quest.

Mobile performs shape checks, prevents obvious duplicate taps, and shows pending
state. Backend repeats all validation, authorizes ownership, handles concurrency,
and is the only reward authority.

### Scheduling boundaries

One-time quests may start immediately or at a future instant and may have an
optional due instant. Without a due instant they do not expire. Recurring quests
use the recurrence rules below. Mobile-generated reminders and device background
execution do not create occurrences.

### Examples and boundaries

- Valid: one-time “Register for race,” 20 XP, due next Friday.
- Valid: zero-XP recurring “Take medication” if product use is appropriate; its
  accepted completion can qualify for a streak.
- Invalid: negative or fractional XP; orphan quest; cross-user campaign; client
  awards reward before acceptance.
- Invalid: a completion submitted against a definition without an occurrence.
- Boundary: two devices complete one occurrence; database uniqueness permits one
  active completion and both receive the canonical result.
- Boundary: reward changes from 10 to 20 after today's occurrence exists; today
  remains 10 and later generated occurrences use 20.

## #3 — One-time and recurring quests

### Distinction and identity

A one-time definition creates exactly one occurrence. A recurring definition
describes a schedule; backend generation creates distinct occurrences. A recurring
definition is never itself completed.

Recurring occurrence identity is unique by `(quest_id, occurrence_local_date)`.
MVP schedules therefore produce at most one occurrence per local date. Each
occurrence also stores schedule-rule version, scheduled local date/time, timezone
snapshot, resolved UTC instant, reward snapshot, and generation timestamp. Worker
retries must return the existing occurrence rather than create another.

### Supported recurrence grammar

MVP supports:

- daily, every calendar day;
- weekly, one or more selected weekdays; and
- monthly, one selected day of month.

Intervals greater than one, cron expressions, multiple times per day, yearly rules,
exception calendars, grace days, and user-authored rule code are deferred. A
monthly day absent from a month is skipped, not clamped to month end.

The start local date is inclusive. Optional end condition is either an inclusive
end local date or a maximum occurrence count, never both. No end condition means
open-ended. Future occurrences are not completable before their availability
instant.

### Missed, skipped, edited, and archived periods

- An available occurrence not completed before its optional eligibility window
  closes becomes `expired`; it is not auto-completed and earns nothing.
- A schedule with no matching date creates no occurrence for that period.
- Missed worker execution is recovered idempotently for dates that should exist.
- A user cannot backdate an ad hoc occurrence.
- Schedule, timezone, and reward edits affect only occurrences not yet generated.
  Generated occurrences, including generated future ones, keep their snapshots.
- Existing completions and expired occurrences are never rewritten by an edit.
- Archiving stops future generation and blocks completion. Generated occurrences
  retain state and history. Restoration resumes from the restoration effective
  date; archived dates are not backfilled.
- Changing a one-time quest schedule cannot move a completed occurrence.

Backend owns recurrence calculation and occurrence generation. The saved quest
timezone is an IANA identifier. DST resolution and timezone edits follow
[time and timezone rules](time-and-timezone.md).

### Examples and implementation boundary

- Daily quest starting March 1 generates keys for March 1, March 2, and so on.
- Monthly day 31 generates January 31, skips February, and generates March 31.
- Weekly Monday quest archived Sunday and restored Tuesday does not backfill Monday.
- Invalid: Android generates an occurrence while offline and awards XP for it.
- Invalid: editing a schedule deletes an already-completed occurrence.
- Boundary: duplicate worker runs for the same local date resolve to one row by the
  unique occurrence key.

Stage 1 defines these semantics only. Recurrence storage, workers, schedulers,
reminders, APIs, and mobile screens belong to later stages.
