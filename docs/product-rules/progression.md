# Progression and achievements

This document is normative for issues #7–#11.

## Progression invariants

1. Only accepted backend events change authoritative progression.
2. One occurrence has at most one active completion and one active XP award.
3. Every XP delta has an immutable source, reason, idempotency relation, and server
   timestamp.
4. Authoritative XP is an integer and never below zero.
5. Level is a pure function of authoritative XP and one versioned level curve.
6. At most one qualifying completion credits a user-global streak day.
7. Achievement rules evaluate authoritative records; unlock identity is unique and
   immutable.
8. Reversal compensates history. It never silently edits a reward or relocks an
   achievement.
9. Mobile presentation events are not progression events.
10. Replay, reordering, offline delay, restart, and multi-device concurrency produce
    the same final state as one correctly ordered logical action set.

## #7 — XP award and reversal

### Award model

In the MVP, only acceptance of an eligible quest occurrence completion awards XP.
Bonuses, manual adjustments, purchases, evidence, social actions, and client events
do not award XP.

`reward_xp` is a nonnegative whole number defined on the quest and copied to each
occurrence when that occurrence is generated. A one-time occurrence receives its
snapshot at quest creation. No fractional XP or rounding exists. Later reward
edits affect only later occurrences.

Backend writes one append-only ledger entry for every accepted completion,
including zero-XP awards for complete audit linkage:

| Field | Rule |
|---|---|
| user | Authenticated owner; immutable. |
| amount | Integer `>= 0` for award; exact negative award amount for reversal. |
| reason | Versioned enum such as `quest_completion` or `completion_reversal`. |
| source | Completion ID for award; reversal ID plus original award ID for compensation. |
| idempotency | Unique source/reason relation and originating mutation ID. |
| time/order | Server timestamps and per-user event sequence. |
| rule snapshot | Reward value and rule version used. |

Database constraints, transaction boundaries, and application validation must all
protect uniqueness. An application-only “already processed” check is insufficient.

### Reversal and total

Reversing a completion appends one ledger delta equal to the negative original
award. It does not edit or delete that award. Replaying reversal returns the same
compensation. Recompletion, when eligible, creates a new completion and new award.

Authoritative XP is the sum of ledger amounts. A valid history cannot produce a
negative total. A transaction that would do so is rejected and flagged for
integrity repair; display code must not clamp corrupt data while hiding the error.

Offline mobile may show “completion pending” but not confirmed XP. After
synchronization it presents the server delta and total. Timeout after server commit
followed by replay returns the original award and cannot add another.

### Examples

- A 10-XP occurrence completed twice through rapid taps creates one `+10` entry.
- Reversal creates `-10`; total returns to its prior value and both entries remain.
- Eligible recompletion creates a new `+10`; three linked entries explain the net.
- Reward edited from 10 to 20 after occurrence generation: that occurrence remains
  10.
- Invalid: mobile increments cached total and later sends only the new total.

## #8 — Level progression

### Threshold model

Level definitions are versioned backend configuration, not mobile constants. Each
curve contains integer levels beginning at level 1 and nonnegative integer
`minimum_total_xp` thresholds:

- level 1 threshold is 0;
- level numbers are contiguous and thresholds strictly increase;
- each level appears once;
- no threshold is fractional or negative;
- a curve is immutable after activation; changes create a new version; and
- absence of a next threshold means the highest configured level, not an invented
  maximum.

Final numeric thresholds are intentionally not selected in Stage 1. A curve cannot
be activated until it passes the validation rules above. The active curve version
is stored with derivation/audit output.

The authoritative level is the greatest configured level whose threshold is less
than or equal to authoritative XP. Exact-threshold XP belongs to the new level.
XP reversal may lower the level. Reconciliation records a level change event but
does not add or remove XP.

### Authority versus presentation

Backend returns current level, XP, curve version, next threshold when present, and
stable level-change event IDs. Mobile may animate a confirmed level-up or
level-down once. It records presentation acknowledgment separately from level
state; deleting app cache can never change authority.

After reconnection or restart, mobile reconciles event IDs and current level. It
must not infer a new event merely because cached level differs. Across devices, an
atomic user-level presentation claim permits at most one full level-change
celebration; all devices display the resulting level after refresh.

### Boundary examples

- XP exactly one point below threshold stays at prior level.
- XP exactly equal to threshold advances.
- Reversal below threshold lowers level and emits one confirmed change event.
- Replaying the completion or reopening the app emits no duplicate change event.
- Invalid curve with equal adjacent thresholds is rejected before activation.

## #9 — Streak calculation

### Selected model

MVP has one user-global daily activity streak. Per-campaign, per-quest, weekly,
grace-period, freeze, repair-token, and manual streak models are deferred.

An active accepted completion of any eligible occurrence qualifies, including a
zero-XP occurrence. Multiple qualifying completions on one effective local date
credit one streak day.

The backend derives a set of qualifying local dates from active completions:

- recurring completion uses the occurrence's backend-generated
  `occurrence_local_date`;
- one-time completion uses `server_received_at` converted with the saved user
  timezone effective when the request was accepted.

Device-observed time and a user-typed date never select a streak day. This narrow
recurring rule permits late synchronization without trusting device time because
the occurrence date already came from server recurrence.

### Current and longest streak

A run is a maximal sequence of consecutive qualifying local dates. Longest streak
is the greatest run length. Current streak is the run ending today or yesterday in
the user's current saved timezone; it becomes zero after an entire intervening
local day has ended without qualifying activity. There is no grace period.

Reversal removes that completion from the qualifying set. If another active
completion remains on the same day, the day stays credited. Backend recalculates
from the earliest affected date through the current date and updates current and
longest streak from authoritative history. Audit retains prior derived values and
the event that changed them.

Timezone changes never rebucket historical streak days. They apply to future
one-time receipts and future recurrence generation. The user-local “today” used to
display current streak uses the current saved timezone. A timezone change alone
does not add a qualifying date or reward.

### Worked examples

1. **Midnight:** saved zone is `America/Halifax`. One-time completions accepted at
   23:59 Monday and 00:01 Tuesday credit Monday and Tuesday: streak 2.
2. **Same day:** three Tuesday completions credit one Tuesday, not streak 3.
3. **Missed day:** activity Monday and Wednesday has two runs of 1; Tuesday's full
   absence breaks the streak.
4. **Offline recurring:** Monday recurrence is completed offline and accepted
   Wednesday. It credits Monday because server-generated occurrence date is Monday;
   XP is awarded Wednesday but ordered by the acceptance event.
5. **Offline one-time:** device claims Monday but server accepts Wednesday. It
   credits Wednesday; device clock cannot backfill Monday.
6. **Travel:** device changes from Halifax to Tokyo without updating saved
   preference. Halifax remains authoritative. After an accepted timezone update,
   only future dates use Tokyo.
7. **DST:** daily occurrences retain distinct local dates even when UTC intervals
   are 23 or 25 hours, so consecutive local dates remain consecutive streak days.
8. **Reversal:** Monday and Tuesday form streak 2. Reversing Monday leaves Tuesday
   as run 1. If a second Monday completion remains active, streak stays 2.

## #10 — Achievement progress and unlocks

### Definition and progress models

Achievement definitions live only on the backend and contain stable ID, immutable
rule version, visibility, authoritative event inputs, progress model, threshold,
unlock presentation metadata, and retroactive-evaluation policy.

MVP supports deterministic models over authoritative data:

- boolean condition;
- monotonic or recalculable counter;
- maximum observed value;
- count of distinct authoritative source IDs; and
- threshold over XP, level, streak, campaign, quest, or completion facts.

Arbitrary client expressions and client-provided progress are forbidden.

Evaluation is idempotent after relevant accepted or reversed events and may also
run as a reconciliation worker. Locked progress is recalculated from current
authoritative records after reversal. The stored definition version identifies the
rule applied. Retroactive evaluation must be explicit per definition; default is
enabled for existing authoritative history when a definition version is first
activated.

### Unlock invariant

The first satisfied evaluation atomically persists one unlock unique by
`(user_id, definition_id, rule_version)`. Its stable unlock ID and
`unlocked_at` never change. Duplicate evaluation, worker retry, event replay, or
two devices cannot create another.

Unlocked achievements never relock. A later reversal may reduce recalculated
progress, but the unlock remains as a historical accomplishment and records that
current progress is below its original threshold when relevant. New rule versions
do not replace old unlock identity.

An offline completion can trigger evaluation only after backend acceptance.
Mobile cannot show confirmed unlock before synchronization.

### Presentation separation

Unlock state and presentation state are separate. Backend creates one stable
presentation event after persisting unlock. A device with an authenticated session
atomically claims the user-level event before full celebration, preventing duplicate
celebrations across devices. All devices may show the unlocked item in collections.

If the app was closed or offline, its next reconciliation fetches unclaimed events,
claims one, and presents in event-sequence order. If another device already claimed
it, the app updates the collection without repeating full presentation. Dismissal
or app termination after claim marks it available in in-app history, not as a new
unlock. Push delivery is optional and never the source of unlock truth.

Examples:

- Two workers evaluate the same threshold concurrently; uniqueness creates one
  unlock and both reconcile to its ID.
- A completion is reversed before a locked counter reaches threshold; recalculation
  lowers progress and creates no unlock.
- A completion is reversed after unlock; progress may fall, but the immutable
  unlock remains.
- An offline completion appears to satisfy a rule on device; no unlock is shown
  until backend accepts and evaluates it.

## #11 — Visible and hidden achievements

### Visibility and presentation states

Definition visibility is one of:

| Visibility before unlock | Mobile response before unlock | After unlock |
|---|---|---|
| `visible` | Stable public ID, name, description, icon key, accessible label, and server-computed progress/threshold when explicitly marked exposable. | Full metadata, progress, and unlock time. |
| `progress_hidden` | Public ID, name, description, icon key, accessible label; no numeric progress, threshold, event criteria, or rule details. | Full user-facing metadata and unlock time; internal rule stays private. |
| `secret` | Only a generic “Secret achievement” placeholder and generic accessible label; no stable rule ID, name, description, icon, progress, threshold, criteria, or ordering clue that identifies the rule. | Full user-facing metadata and unlock time; internal executable rule stays private. |

Presentation state is `locked` or `unlocked`; `secret` is visibility, not a
lifecycle state. The backend constructs responses from an allowlist. Mobile bundles,
editable storage, notification payloads, logs, and analytics must not contain
secret criteria.

### Accessibility and privacy

- Locked visible items expose text equivalents for icons and do not communicate
  status by color alone.
- Secret placeholders use a meaningful generic screen-reader label, not silence or
  a misleading unlocked label.
- Unlocked presentation includes text and non-audio/non-motion equivalents and
  respects reduced-motion, sound, and haptic settings when later implemented.
- Lock-screen notifications default to generic, non-sensitive wording. Full details
  are fetched after authentication and ownership checks.
- Denying notification permission does not block unlock, history, collection access,
  or delayed in-app presentation.

Only backend evaluation can unlock. Changing local flags, progress, cache, device
clock, timezone, push payload, or deep-link parameters cannot create an unlock.

Examples:

- A locked `visible` “Complete 10 quests” item may show `7/10` only when its
  definition allows exposable progress.
- A `progress_hidden` item can show its name and icon but never `7/10` or hidden
  criteria before unlock.
- A `secret` API item is a generic placeholder before unlock; inspecting mobile
  storage reveals no rule identifier or description.
- An unlock received while notifications are denied remains available through
  authenticated in-app history with accessible text.
