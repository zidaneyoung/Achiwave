# Achiwave documentation

## Development and acceptance

- [Stage 2 local development](local-development.md)
- [Stage 2 acceptance audit](testing/stage-2-acceptance.md)
- [Stage 3 PostgreSQL schema](database/stage-3-schema.md)
- [Stage 3 acceptance audit](testing/stage-3-acceptance.md)
- [Stage 4 authentication and account security](security/stage-4-authentication.md)
- [Stage 4 acceptance audit](testing/stage-4-acceptance.md)
- [Stage 5 visual direction](design/stage-5-visual-direction.md)
- [Stage 5 mobile design system](design/stage-5-design-system.md)
- [Stage 5 acceptance audit](testing/stage-5-acceptance.md)
- [Stage 6 campaigns and quests](features/stage-6-campaigns-and-quests.md)
- [Stage 6 acceptance audit](testing/stage-6-acceptance.md)

This index is the normative entry point for Stage 1 product rules. If a later
implementation conflicts with these documents, the implementation is wrong until
an explicit replacement decision is accepted and all affected documents,
contracts, tests, and migrations are updated together.

## Product rules

- [Domain model, glossary, ownership, and recurrence](product-rules/domain-model.md)
  — issues #1–#3 and shared vocabulary.
- [Quest and campaign state transitions](product-rules/state-transitions.md)
  — issues #4–#6.
- [XP, levels, streaks, and achievements](product-rules/progression.md)
  — issues #7–#11 and progression invariants.
- [Time, timezone, and timestamp authority](product-rules/time-and-timezone.md)
  — issues #12 and #16.
- [Offline and multi-device synchronization](product-rules/offline-and-synchronization.md)
  — issues #13–#14.
- [History, archival, and deletion](product-rules/history-and-deletion.md)
  — issue #15.
- [MVP boundary](product-rules/mvp-boundary.md) — issue #17.
- [Stage 1 issue traceability](product-rules/stage-1-traceability.md) — exact
  #1–#17 mapping and verification result.

- [Quest authoring configuration](product-rules/quest-authoring.md) â€” accepted
  Stage 6 category, difficulty, and configured-reward contracts.

## Architecture decisions

- [ADR index](architecture/decisions/README.md)
- [Stage 1 acceptance audit](testing/stage-1-acceptance.md)

## Normative language and precedence

`Must`, `must not`, and `only` are requirements. `May` is an allowed choice.
Examples illustrate rules but do not override them.

Precedence is:

1. accepted architecture decision records;
2. product-rule documents;
3. acceptance audit and traceability;
4. examples and non-normative backlog scripts.

The live Stage 1 milestone and issues #1–#17 define scope. Issue #18 and later
issues are implementation work outside Stage 1.

## Non-negotiable authority boundary

Backend owns user isolation, validation, recurrence, accepted completions,
progression timestamps, XP, levels, streaks, achievement evaluation, duplicate
prevention, synchronization results, and durable history. Mobile owns input,
presentation, native feedback, permission handling, secure local data, and the
supported pending-operation queue. Device data can propose context; it cannot
create authoritative progression.
