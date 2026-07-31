# Stage 1 acceptance audit

This audit is executable by another developer without product assumptions outside
the repository and live GitHub issues #1–#17.

## Audit outcome rule

Stage 1 passes only when every automated check below succeeds and every manual
criterion is evidenced in the linked rule section. Any missing evidence is
`Unable to Verify`; any contradiction or failed check is `Fail`. Stage 2 remains
blocked unless every row is `Pass`.

## Preconditions

1. Confirm the live milestone is
   `Stage 1 - Product Rules and Domain Foundation`.
2. Confirm its scope is issues #1–#17 and inspect their current bodies/dependencies.
3. Confirm issue #18 is not included.
4. Record branch and `git status --short`; preserve pre-existing unrelated changes.
5. Read root README, `AGENTS.md`, this index, and each linked product-rule document.

## Expected files

Run from repository root:

```powershell
$expected = @(
  'AGENTS.md',
  'docs/README.md',
  'docs/product-rules/domain-model.md',
  'docs/product-rules/state-transitions.md',
  'docs/product-rules/progression.md',
  'docs/product-rules/time-and-timezone.md',
  'docs/product-rules/offline-and-synchronization.md',
  'docs/product-rules/history-and-deletion.md',
  'docs/product-rules/mvp-boundary.md',
  'docs/product-rules/stage-1-traceability.md',
  'docs/architecture/decisions/README.md',
  'docs/architecture/decisions/0001-server-authoritative-progression.md',
  'docs/architecture/decisions/0002-timestamp-and-timezone-authority.md',
  'docs/architecture/decisions/0003-idempotent-offline-mutations.md',
  'docs/architecture/decisions/0004-reward-and-history-reversal.md',
  'docs/architecture/decisions/0005-multi-device-conflict-resolution.md',
  'docs/testing/stage-1-acceptance.md'
)
$missing = $expected | Where-Object { -not (Test-Path -LiteralPath $_) }
if ($missing) { $missing; exit 1 }
"PASS: $($expected.Count) expected files exist"
```

## Link check

Check every relative Markdown link in README, `AGENTS.md`, and `docs/`:

```powershell
$files = @((Get-Item README.md), (Get-Item AGENTS.md)) +
  @(Get-ChildItem docs -Recurse -File -Filter *.md)
$broken = @()
foreach ($file in $files) {
  $text = Get-Content -LiteralPath $file.FullName -Raw
  foreach ($match in [regex]::Matches($text, '\[[^\]]+\]\(([^)]+)\)')) {
    $target = $match.Groups[1].Value.Trim('<','>')
    if ($target -match '^(?:[a-z]+:|#)') { continue }
    $pathPart = [uri]::UnescapeDataString(($target -split '#', 2)[0])
    $resolved = [IO.Path]::GetFullPath((Join-Path $file.DirectoryName $pathPart))
    if (-not (Test-Path -LiteralPath $resolved)) {
      $broken += "$($file.FullName) -> $target"
    }
  }
}
if ($broken) { $broken; exit 1 }
"PASS: relative Markdown links resolve"
```

## Traceability and unresolved-marker checks

```powershell
$trace = Get-Content docs/product-rules/stage-1-traceability.md -Raw
$missingIssues = 1..17 | Where-Object { $trace -notmatch "\|\s*#$($_)\s*\|" }
if ($missingIssues) { $missingIssues; exit 1 }
"PASS: issues #1 through #17 have traceability rows"

$markers = @('T' + 'BD', 'TO' + 'DO', 'FIX' + 'ME')
$hits = Get-ChildItem README.md,AGENTS.md,docs -Recurse -File |
  Select-String -Pattern $markers
if ($hits) { $hits; exit 1 }
"PASS: no unresolved markers"
```

Confirm each traceability row names one file, exact section, concrete evidence, and
`Pass`, `Fail`, or `Unable to Verify`. Confirm no success is inferred from planned
implementation or device behavior.

## Manual product-rule audit

| Criterion | Evidence to inspect | Result |
|---|---|---|
| #1–#17 each have rule, boundary, owner, examples, exceptions, and edge behavior. | [Traceability table](../product-rules/stage-1-traceability.md) and exact linked sections. | **Pass** |
| Android, iOS, API, worker, and database responsibilities agree. | [Responsibility matrix](../product-rules/domain-model.md#responsibility-matrix) and authority ADR. | **Pass** |
| Campaign/quest terms are consistent and no quest can belong to multiple campaigns. | Glossary plus issues #1–#3 sections. | **Pass** |
| Every quest/campaign state and transition is explicit. | Definition, occurrence, and campaign transition tables plus forbidden examples. | **Pass** |
| Completion, replay, duplicate, reversal, and recompletion cannot duplicate reward. | Issue #6, XP invariant, offline replay, and conflict matrix. | **Pass** |
| XP is integer, append-only, reconstructable, and compensated on reversal. | Issue #7 and ADR 0004. | **Pass** |
| Level and streak derivation are deterministic at exact/timezone boundaries. | Issues #8–#9 worked examples and timestamp rules. | **Pass** |
| Achievement evaluation/unlock remains backend-only and exactly once. | Issues #10–#11 and hidden-response allowlists. | **Pass** |
| Secret rules and private notification/queue data are concealed. | Issue #11, offline privacy, MVP security boundary. | **Pass** |
| UTC, IANA timezone, local date, server time, and device metadata differ clearly. | Issues #12/#16 matrices and ADR 0002. | **Pass** |
| Clock/timezone edits cannot independently award progression. | Time manipulation rules and streak examples. | **Pass** |
| Offline queue has stable identity, states, failures, rollback, retry, and logout rules. | Issue #13 lifecycle and examples. | **Pass** |
| Every required device conflict has winner, rejection, final state, and visible outcome. | Issue #14 conflict matrix. | **Pass** |
| Archive/delete/restore/account deletion preserve integrity and privacy. | Issue #15 effects matrix and legal exception. | **Pass** |
| MVP separates decisions from later implementation and gates Stage 2. | Issue #17 explicit boundary and stage gate. | **Pass** |
| README and docs index are navigable; no Stage 2 implementation exists in the change. | Link check and final diff path review. | **Pass** |

## Determinism spot checks

Trace each case through tables and verify one outcome:

1. Two devices complete the same occurrence.
2. Response is lost after server commit and the mutation is replayed.
3. Completion and archive race in both commit orders.
4. Reversal races a stale recompletion.
5. Daily recurrence crosses spring-forward and fall-back.
6. Phone changes zone without updating saved preference.
7. Recurring and one-time completions synchronize late.
8. Reversal removes the only qualifying completion from a streak day.
9. Duplicate achievement evaluation runs on two workers.
10. App was closed for an unlock and another device claims presentation first.
11. Quest is archived while completion is pending.
12. User confirms logout with private pending operations.

Each resolves in the current documents without client authority or silent history
mutation; result is **Pass**.

## Recorded Stage 1 documentation audit

- Date: 2026-07-30
- Scope: documentation only, issues #1–#17
- Expected-file check: **Pass**
- Relative-link check: **Pass**
- Traceability mapping check: **Pass**
- Unresolved-marker scan: **Pass**
- Terminology/state/conflict/manual audit: **Pass**
- Stage 2 code exclusion and final diff review: **Pass**
- Device/runtime evidence: not applicable to this documentation-only stage; no
  device, backend, database, queue, notification, or recurrence implementation is
  claimed.

Final result: **Pass**. Stage 1 domain documentation satisfies its acceptance audit;
Stage 2 may use it as the implementation contract.
