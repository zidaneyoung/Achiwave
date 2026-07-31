# MVP feature boundary

This document is normative for issue #17 and separates Stage 1 decisions from
later implementation.

## #17 — In-scope product capabilities

The planned MVP is a native personal-progress product for Android and iOS:

- one authenticated user owns private campaigns and quests;
- campaigns contain zero or more one-time and recurring quests;
- one-time, daily, selected-weekday weekly, and day-of-month monthly occurrence
  semantics described in Stage 1;
- explicit quest completion, reversal, archive, and restore;
- backend-authoritative XP ledger, configurable level curve, user-global daily
  streak, and rule-based achievements;
- visible, progress-hidden, and secret achievement presentation;
- durable history and privacy-aware account deletion;
- cached read-only mobile data and a durable offline completion queue;
- idempotent replay, deterministic conflict handling, stale-version detection, and
  multiple registered devices;
- native feedback and privacy-safe notification/deep-link presentation when later
  implemented; and
- accessible alternatives to color, audio, motion, and hidden-state presentation.

These are product capabilities, not Stage 1 code deliverables.

## Platform and authority direction

- Mobile direction: React Native, TypeScript, Expo, and Expo Router targeting native
  Android and iOS applications.
- Backend direction: FastAPI services, PostgreSQL persistence, and backend workers
  for authoritative recurrence and event processing.
- No user-facing web or desktop application is required for MVP. Responsive desktop
  layouts, hover behavior, browser offline support, and desktop notifications are
  unsupported.
- Backend owns identity enforcement, validation, recurrence, accepted timestamps,
  progression, duplicate prevention, synchronization results, and history.
- Mobile owns input, local presentation, native feedback, secure local storage,
  permission handling, push/deep-link handling, and the supported completion queue.

## Campaign, quest, and progression boundary

- Quests belong to exactly one campaign and cannot be moved.
- Campaign completion is derived. A recurring definition is never completed.
- Recurrence has at most one occurrence per local date and is generated only by the
  backend.
- XP comes only from accepted occurrence completion in MVP and uses an append-only
  integer ledger.
- Level thresholds are versioned configurable data; final numeric values are a
  later product configuration.
- One user-global daily streak has no grace, freeze, repair, or manual backdating.
- Achievement progress and unlocks are evaluated only on the backend. Unlocks are
  permanent; presentation is deduplicated separately.

## Offline and synchronization boundary

- Cached campaigns, quests, occurrences, progression, and achievement presentation
  may be viewed offline and are clearly stale.
- Only quest occurrence completion is queued offline in MVP.
- Offline campaign/quest edits, archive/restore, reversal, timezone changes,
  registration, account deletion, and achievement claims are unsupported.
- Stable per-user client mutation IDs, canonical payload hashes, resource versions,
  unique completion/reward constraints, and server event sequence provide
  deterministic replay and conflict behavior.
- Pending, confirmed, retryable failure, permanent failure, and cancelled outcomes
  must be distinguishable.
- Peer-to-peer sync, unbounded offline history, device-authoritative merging, and
  generic last-write-wins for rewards are unsupported.

## Notification permission and delivery

Notification permission is optional and requested only in context after explaining
the benefit. Denial, permanent denial, unavailable capability, disabled category,
or push failure must not block campaigns, quest completion, progression,
achievement access, or in-app history. Mobile tracks permission state, does not
repeatedly prompt after denial, and may direct the user to system settings.

Notifications are hints, not authority. Payloads use stable event/route identifiers
and minimal non-sensitive content. Protected targets are fetched after
authentication and ownership validation; payload data cannot authorize a deep
link. Provider acceptance does not prove delivery or viewing. Local reminders never
generate authoritative recurrence.

Push delivery, token registration, platform credentials, foreground/background
handlers, and reminder scheduling are later implementation and device-verification
work.

## Evidence and attachments

Evidence capture, camera/photo/document permissions, file upload, media
compression, content moderation, public evidence, and attachment-backed completion
are outside the defined MVP boundary. Stage 1 completion is explicit user intent
validated against occurrence state, with no attachment required or accepted.

A later accepted product change may add evidence while preserving backend
ownership, file validation, private-by-default visibility, secure upload, deletion,
and the rule that mobile evidence cannot award progression by itself.

## Initial privacy and security assumptions

- Backend authentication establishes identity and authorizes every user-owned
  resource. Biometrics, if later added, only unlock local credentials.
- Long-lived credentials use OS secure storage; tokens never enter ordinary queue
  records, URLs, logs, notification payloads, or public configuration.
- Private cache and queue data are account-partitioned and cleared on confirmed
  logout/account switch.
- Secret achievement rules never ship in mobile bundles or editable state.
- Device timestamps, timezone, identifiers, and push tokens are minimized, treated
  as private metadata, and deleted/de-identified with the account.
- Lock-screen notification content is generic by default; richer state requires
  authenticated in-app fetch.
- HTTPS is required in production. Rooted/compromised-device limitations and
  transport hardening are later security implementation work.

Password rules, verification, token lifetimes/rotation, recovery, maximum devices,
offline session duration, biometric fallback, jurisdictional retention periods,
and production secret management are intentionally deferred to their later
security/privacy issues. No Stage 1 rule supplies invented values for them.

## Explicitly deferred capabilities

- all mobile, backend, database, worker, queue, notification, infrastructure, auth,
  and UI implementation;
- final API schemas, persistence models, indexes, migrations, and worker horizons;
- final level thresholds and achievement catalog;
- richer recurrence, multiple daily occurrences, cron, exceptions, grace days,
  shared campaigns, social features, purchases, leaderboards, and admin rewards;
- evidence/attachments and public sharing;
- web/desktop interfaces;
- notification delivery guarantees, critical alerts, email, SMS, and location
  triggers;
- analytics, store submission, production deployment, and legal-policy localization.

## Stage gate

Stage 1 has no dependency. Stage 2 may begin only after
[`stage-1-acceptance.md`](../testing/stage-1-acceptance.md) is executed against the
current documentation and every Stage 1 criterion is `Pass`. A failed or
unverifiable rule criterion blocks dependent implementation until evidence or an
accepted replacement decision resolves it.

Issue #18 belongs to Stage 2 and is not implemented by Stage 1 documentation.

Boundary examples:

- In scope as a rule, later to implement: a daily quest completed offline and
  safely deduplicated after reconnection.
- Outside MVP: two users share one campaign or a browser edits quests.
- Outside Stage 1 but inside later implementation: FastAPI endpoints, mobile
  screens, recurrence workers, notification delivery, and database constraints.
- Forbidden in every stage unless this contract is replaced: device awards XP or a
  notification payload unlocks an achievement.
