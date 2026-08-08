# Stage 6 acceptance audit

## Result

Stage 6 is **in progress**. Issues #108-#123 have verified implementations.
Issues #124-#129 remain to be implemented on the final Stage 6 branch. Issue
#130 and all Stage 7 completion, XP-award, progression, recurrence-worker,
notification, and offline-mutation behavior remain out of scope.

## Traceability

| Issues | Branch | Commits | Pull request / merge | Status |
| --- | --- | --- | --- | --- |
| #108-#113 | `stage-6/campaign-management-108-113` | `26990fb`, `af97617`, `ee2a718`, `240bb9b`, `ff3b4e6`, `da7728c` | [#390](https://github.com/zidaneyoung/Achiwave/pull/390), merged as `c32ee098089d8317fb0fc79b04b4c95f20c7e3ce` | Pass; issues closed |
| #114-#118 | `stage-6/quest-authoring-114-118` | `077ab51`, `adad3f6`, `75fc7df`, `1c502b8`, `2c74811` | [#391](https://github.com/zidaneyoung/Achiwave/pull/391), merged as `f2658ec771b9e2670d3aed6409c73c8180f625e8` | Pass; issues closed |
| #119-#123 | `stage-6/quest-planning-119-123` | `6a1b69f`, `7f937c5`, `47a7012`, `1ca6c0b`, `189cfa8` | [#392](https://github.com/zidaneyoung/Achiwave/pull/392) | Pass locally; pending review/merge |
| #124-#129 | `stage-6/quest-discovery-integrity-124-129` | Pending | Pending | Not started |

Review-fix commits on the first two branches were `ff0913f`, `c125f12`, and
`23bcbce`. No implementation commit was made directly on `main`.

## Accepted quest-authoring contract

The earlier contract gap is resolved in
[`quest-authoring.md`](../product-rules/quest-authoring.md):

- category is optional; `null` means Uncategorized, with exact canonical values
  Personal, Health, Learning, Work, and Finance;
- difficulty uses exact Easy, Medium, and Hard values, remains independent from
  XP, and is required for new quests while legacy null rows remain readable;
- new or changed rewards use `0`, `10`, or `20` XP, while legacy configured and
  snapshotted rewards remain readable and are never rewritten; and
- active quest order is an owner-scoped, versioned, replay-safe presentation
  mutation over the complete active set, with archived quests excluded.

The backend exposes the accepted choices to authenticated mobile clients. The
database checks category and difficulty machine values but deliberately retains
only the established nonnegative XP constraint so unknown deployed legacy
rewards cannot be invalidated.

## Verification evidence through #123

Evidence was collected on 2026-08-08 against disposable PostgreSQL 18.4 on host
port 55436 and the clean Stage 6 worktree.

### Backend and migrations

- Pass: full backend regression suite, `168 passed`.
- Pass: Alembic has one head and current revision, `20260808_0081`.
- Pass: `alembic upgrade head` and `alembic check`; no new upgrade operations.
- Pass: real-PostgreSQL tests cover strict category and difficulty values,
  optional/legacy null behavior, all allowed and disallowed reward cases,
  immutable occurrence snapshots, lifecycle preservation, exact reorder sets,
  stale and concurrent writes, replay safety, and canonical contiguous order.
- Pass: authoring and reordering create no XP ledger or progression side effect.

### Mobile

- Pass: all repository mobile scripts, `36 tests` total.
- Pass: TypeScript `tsc --noEmit`.
- Pass: Expo Doctor, `20/20` checks.
- Pass: Android export, `1,323 modules`.
- Pass: category, difficulty, and XP choices use accessible Stage 5 selectors;
  active quest ordering has visible move-up/down controls with 48 dp touch-target
  infrastructure, disabled boundary/ambiguous states, and screen-reader
  announcements. No drag or animation is required.

The Expo checks used the documented non-secret development public environment
values. Generated export artifacts were removed after verification.

## Unable to Verify

This workstation exposes no Android SDK, ADB, Java, emulator, or physical-device
bridge. Emulator/physical-device navigation, TalkBack, keyboard/modal/back
behavior, device font scaling, physical touch targets, and rendered interaction
remain `Unable to Verify`; none are reported as passed from static or bundle
evidence.

## Remaining scope

Stage 6 global acceptance does not yet pass. Quest filtering, pull-to-refresh,
Android date/time pickers, dirty-form protection, archive confirmation, and the
populated historical-integrity suite remain for #124-#129. The final acceptance
audit will replace this section after those issues are implemented, reviewed,
and merged.
