# Stage 6 campaigns and quests

## Status

Stage 6 is implemented through issue #129. It includes campaign management,
one-time quest authoring and planning, owner-scoped discovery, refresh, Android
date/time selection, form-exit protection, archive confirmation, and
PostgreSQL-backed historical-integrity verification.

Issue #130 and all Stage 7 completion, XP-award, progression,
recurrence-worker, notification, and offline-mutation behavior remain out of
scope.

## API contract

The authenticated API uses these Stage 6 routes:

- `POST /api/v1/campaigns`
- `GET /api/v1/campaigns`
- `GET /api/v1/campaigns/{campaign_id}`
- `PATCH /api/v1/campaigns/{campaign_id}`
- `POST /api/v1/campaigns/{campaign_id}/archive`
- `POST /api/v1/campaigns/{campaign_id}/restore`
- `POST /api/v1/campaigns/{campaign_id}/quests`
- `GET /api/v1/quests`
- `GET /api/v1/quests/{quest_id}`
- `PATCH /api/v1/quests/{quest_id}`
- `POST /api/v1/quests/{quest_id}/archive`
- `POST /api/v1/quests/{quest_id}/restore`
- `PUT /api/v1/campaigns/{campaign_id}/quests/order`
- `GET /api/v1/quests/authoring-options`

Unknown request fields are rejected. Ownership always comes from the
authenticated user; client payloads cannot set an owner or authoritative
lifecycle state, timestamp, record version, occurrence, reward event, or
campaign-completion result.

## Campaign behavior

Authenticated owners can create, list, inspect, edit, archive, and restore their
campaigns. Owner filters are applied on the backend. Cross-owner identifiers
return the same not-found result as absent records. Every mutation requires a
stable client mutation identifier; mutations against an existing campaign also
require its current record version, while creation establishes version one.

Campaign archival is reversible and does not delete quest definitions,
occurrences, or progress history. A campaign's completion state remains derived
from authoritative quest obligations; mobile code does not award progress.

Ordinary edits may change the title and optional description. Stable identity,
owner, and direct lifecycle/completion fields are immutable. Accepted semantic
changes increment the record version and use a server timestamp. Stale requests
return a controlled conflict with canonical current state.

## One-time quest behavior

An active campaign can receive a one-time quest with a title, optional
description, configured nonnegative XP value, and optional due date. Creation
atomically creates exactly one authoritative occurrence snapshot. The campaign
assignment and owner are immutable.

Quest definition edits do not rewrite the generated occurrence's reward or
schedule snapshot. Archival and restoration retain the definition and occurrence
history and use append-only progress events for lifecycle changes.

Ordinary quest edits may change title, optional description, category,
difficulty, and configured reward subject to the accepted authoring contract.
Owner, campaign assignment, quest type, stable identity, generated schedule, and
historical occurrence fields are immutable. Moving a quest means archiving the
old definition and creating a new definition in the target campaign.

## Mutation concurrency and replay

Every Stage 6 mutation uses a stable client mutation identifier. Mutations
against an existing campaign or quest require its current authoritative record
version, and quest creation requires the current parent-campaign version;
campaign creation establishes version one. The backend binds the identifier to
the owner, operation, target, and canonical payload in the same transaction as
the change. Reusing it for a different payload returns a controlled conflict.

Campaign and quest archive/restore operations materialize their complete public
response in the private mutation row. An exact retry therefore returns the
original IDs, versions, states, and timestamps even after an inverse transition
or later parent archive, without duplicating a lifecycle event. The same
materialized-response rule applies to quest reordering. Legacy mutation rows
whose nullable response predates this support use current-state fallback; the
backend does not fabricate an unrecoverable historical response.

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
quest-list contracts and drive the implemented #124 server filtering; no
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

## Active quest order

Owners can move active quests up or down through visible buttons. The backend
validates the complete owner-scoped active set and all record versions, writes
contiguous positions in one transaction, and returns the canonical order.
Archived quests are excluded and restored quests append to the active sequence.
Reordering is disabled whenever archived history or another ambiguous view is
shown, and it has no completion, reward, or progression side effect. The original
canonical reorder response is stored with the private mutation record, so an
exact replay returns the same order and versions even after later reorders or
archival.

## Quest discovery and filtering

The authenticated quest browser requests owner-scoped results from
`GET /api/v1/quests`; it does not load private records and filter them on the
device. Campaign, canonical quest status, canonical category (including the
`uncategorized` sentinel), and inclusive due-date bounds combine on the server.
Due-date bounds are interpreted as calendar days in the authenticated user's
saved IANA timezone. Results include authoritative status and campaign context,
use stable campaign/quest ordering, and are paginated.

The default view excludes archived quest definitions and quests contained by an
archived campaign. An explicit Archived status shows archived definitions,
including those beneath archived campaigns, without relabelling active child
definitions. Filter state remains mounted while the user opens a quest and
returns. The Android filter sheet provides selected-state labels, validation,
clear actions, and distinct first-use and filtered-empty states.

## Refresh behavior

Campaign lists, campaign detail, the filtered quest list, and quest detail use
native pull-to-refresh against canonical APIs. A keyed single-flight boundary
prevents duplicate in-flight reads. Existing content, filters, navigation, and
cached data remain visible during ordinary refreshes; refresh failures are shown
separately from initial-load failures. Manual results are announced to assistive
technology. Reduced-motion mode suppresses the animated refresh state and uses a
static live-region status instead; refresh is never described as synchronization
or mutation success.

## Android due-date picker

Quest creation uses the Expo-compatible Android community date/time picker. The
user confirms a date and then a time; cancellation or Android back at either step
leaves the previously committed value unchanged. Both native dialogs receive the
saved IANA timezone, and the readable control shows the selected local intent and
timezone. The client preserves `YYYY-MM-DDTHH:MM` local intent without converting
it to UTC; backend scheduling validation and resolution remain authoritative. A
text fallback remains available outside Android or when a valid saved timezone is
unavailable.

## Form and archive safety

Campaign and quest create/edit screens compare semantic snapshots with their
initial or last canonical state. Trimming-only differences are ignored, while
invalid meaningful input remains dirty. Stack removal, Android system back,
gesture navigation, and other navigation-away actions present one Stage 5
Stay/Discard dialog. Staying retains the memory-only draft; discarding disables
the guard before dispatching the original pending action. A successful committed
submission also disables prevention before navigating. Drafts are never written
to cross-account storage, and account identity is part of each loaded form key.

Campaign and quest Archive buttons open named destructive dialogs. The copy
explains that the item becomes hidden and activity is blocked while occurrences,
completions, rewards, reversals, and audit history remain. Cancel and Archive are
explicit labelled buttons. Pending requests lock both actions and Android dialog
dismissal; a failure remains visible in the open dialog and a retry reuses the
same mutation identifier and record-version payload. Restore is not destructive
and does not require confirmation. Permanent deletion is never offered.

## Historical preservation

Archive and restore are lifecycle changes, not physical deletion. Campaign and
quest identifiers and associations remain stable. Occurrences, completions,
reversals, XP awards and compensations, progress events, removed streak sources,
achievement progress, unlocks, and lifecycle mutation history remain associated
with the original definitions. Archival itself never awards, reverses, or removes
XP and never relocks an achievement. Restoration creates no archived-period
occurrence backfill. Default active views hide archived definitions and archived
parents; owner-authorized archived and detail views retain access to history.
PostgreSQL `ON DELETE RESTRICT` constraints remain unchanged and are exercised by
the Stage 6 acceptance test using their concrete constraint names.

## Android navigation and accessibility

Production campaign and quest screens are reachable from authenticated Expo
Router navigation and use the Stage 5 theme, typography, buttons, fields,
selectors, cards, badges, loading/error/empty states, overlays, offline notices,
and keyboard-aware scroll containers. Controls keep the shared 48 dp minimum
target, do not disable font scaling, use text in addition to colour, expose
names/roles/states, and announce refresh, lifecycle, validation, and failure
results. Lists, forms, filters, and dialogs remain scrollable so required actions
can reflow at narrow viewports and large font scales. Reduced motion suppresses
nonessential refresh animation and reorder controls do not require dragging.

Device-only TalkBack, native picker, keyboard, Android back/gesture, physical
touch-target, viewport, and font-scale behavior require emulator or physical
device evidence and remain explicitly separate from static, unit, type-check,
and export results.
