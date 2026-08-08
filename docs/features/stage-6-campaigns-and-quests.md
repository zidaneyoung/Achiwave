# Stage 6 campaigns and quests

## Status

Stage 6 is partially implemented through issue #122. Campaign management
(#108-#113), one-time quest authoring (#114-#118), and optional one-time due
dates (#119), optional quest categories (#120), quest difficulty (#121), and
allowed configured XP choices (#122) are implemented.

Issues #123-#129 remain unimplemented. Issue #130 and all Stage 7 completion,
XP-award, progression, recurrence-worker, notification, and offline-mutation
behavior remain out of scope.

## Campaign behavior

Authenticated owners can create, list, inspect, edit, archive, and restore their
campaigns. Owner filters are applied on the backend. Cross-owner identifiers
return the same not-found result as absent records. Mutating requests require a
stable client mutation identifier and current record version.

Campaign archival is reversible and does not delete quest definitions,
occurrences, or progress history. A campaign's completion state remains derived
from authoritative quest obligations; mobile code does not award progress.

## One-time quest behavior

An active campaign can receive a one-time quest with a title, optional
description, configured nonnegative XP value, and optional due date. Creation
atomically creates exactly one authoritative occurrence snapshot. The campaign
assignment and owner are immutable.

Quest definition edits do not rewrite the generated occurrence's reward or
schedule snapshot. Archival and restoration retain the definition and occurrence
history and use append-only progress events for lifecycle changes.

## Due-date contract

The creation API accepts local scheduling intent as
`YYYY-MM-DDTHH:MM`. The authenticated user's saved IANA timezone is authoritative
unless the request explicitly supplies another timezone accepted by the existing
timezone validator. The backend:

- validates syntax, calendar values, timezone identity, and future ordering;
- resolves DST gaps to the first valid instant after the gap;
- selects the earlier offset during a DST overlap;
- stores the resolved UTC instant and IANA context on the quest;
- copies the UTC expiry, timezone, and timezone-data version into the occurrence
  snapshot; and
- rejects later schedule fields on quest edits, so completed and historical
  occurrences cannot move.

The API derives `due_status` from server time and authoritative stored state.
Mobile screens never compare the due instant to the device clock. They format the
server instant in the quest timezone using the user's Stage 4 date-format
preference. The canonical due fields are exposed on quest detail and campaign
quest-list contracts for the later #124 server-filter implementation; no
historical value is recalculated.

## Category contract

Quest categories use the canonical values and labels in
[`quest-authoring.md`](../product-rules/quest-authoring.md). Category is optional;
stored `null` means Uncategorized. Existing definitions remain uncategorized and
no occurrence or reward snapshot is rewritten. The backend rejects unknown or
non-canonical values and exposes the choices through its authenticated
authoring-options contract.

## Difficulty contract

New quests require an Easy, Medium, or Hard difficulty from the canonical values
in [`quest-authoring.md`](../product-rules/quest-authoring.md). Difficulty remains
independent from configured XP and has no completion or reward authority. Legacy
null values remain readable as Not set, are not backfilled, and must be replaced
with a canonical value when explicitly changed.

## Configured reward contract

New or changed rewards use the centralized `0`, `10`, or `20` XP choices in
[`quest-authoring.md`](../product-rules/quest-authoring.md). These choices remain
independent from difficulty and never award XP during authoring. Legacy values
outside the choices stay readable and may remain unchanged; occurrence snapshots
and historical rewards are never rewritten.
