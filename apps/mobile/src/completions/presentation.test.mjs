import assert from "node:assert/strict";
import test from "node:test";

import {
  beginCompletionPresentation,
  clearCompletionPresentations,
  confirmCompletionPresentation,
  failCompletionPresentation,
  getCompletionPresentation,
  refreshCompletionCanonical,
} from "./presentation.ts";

function quest(overrides = {}) {
  return {
    id: "quest",
    campaignId: "campaign",
    campaignRecordVersion: 4,
    campaignStatus: "active",
    occurrence: {
      id: "occurrence",
      status: "available",
      recordVersion: 2,
      activeCompletionId: null,
    },
    ...overrides,
  };
}

function input() {
  return {
    occurrenceId: "occurrence",
    expectedOccurrenceVersion: 2,
    clientMutationId: "mutation",
    deviceObservedAt: "2026-08-12T12:00:00Z",
    deviceTimezoneName: "UTC",
  };
}

function result() {
  return {
    outcome: "completed",
    occurrence: {
      id: "occurrence",
      status: "completed",
      recordVersion: 3,
      completedAt: "2026-08-12T12:00:01Z",
      reversedAt: null,
    },
    completion: { id: "completion", eventSequence: 7 },
    campaign: {
      id: "campaign",
      status: "completed",
      recordVersion: 5,
      completedAt: "2026-08-12T12:00:01Z",
    },
    progressEvents: [{ eventSequence: 8 }],
  };
}

test("pending overlay keeps canonical state separate across navigation and refetch", async () => {
  await clearCompletionPresentations();
  beginCompletionPresentation("owner", quest(), input());
  const afterNavigation = getCompletionPresentation("owner", "occurrence");
  assert.equal(afterNavigation?.phase, "pending");
  assert.equal(afterNavigation?.canonical.occurrenceStatus, "available");

  refreshCompletionCanonical("owner", quest({ campaignRecordVersion: 5 }));
  const afterRefetch = getCompletionPresentation("owner", "occurrence");
  assert.equal(afterRefetch?.phase, "pending");
  assert.equal(afterRefetch?.canonical.campaignVersion, 5);
});

test("canonical result is stored before pending presentation becomes synchronized", async () => {
  await clearCompletionPresentations();
  beginCompletionPresentation("owner", quest(), input());
  const confirmed = confirmCompletionPresentation("owner", result());
  assert.equal(confirmed.confirmedResult?.completion.id, "completion");
  assert.equal(confirmed.phase, "synchronized");
  assert.equal(confirmed.canonical.occurrenceStatus, "completed");
  assert.equal(confirmed.canonical.campaignStatus, "completed");
  assert.equal(confirmed.canonical.eventSequence, 8);
  assert.equal("xp" in confirmed, false);
});

test("out-of-order completion responses cannot regress newer canonical state", async () => {
  await clearCompletionPresentations();
  beginCompletionPresentation("owner", quest(), input());
  const current = confirmCompletionPresentation("owner", result());

  refreshCompletionCanonical("owner", quest({
    campaignRecordVersion: 5,
    campaignStatus: "completed",
    occurrence: {
      id: "occurrence",
      status: "completed",
      recordVersion: 3,
      activeCompletionId: "completion",
    },
  }));
  assert.equal(getCompletionPresentation("owner", "occurrence")?.canonical.eventSequence, 8);

  const staleResult = result();
  staleResult.occurrence.recordVersion = 2;
  staleResult.campaign.recordVersion = 4;
  const delayed = confirmCompletionPresentation("owner", staleResult);
  refreshCompletionCanonical("owner", quest({
    campaignRecordVersion: 4,
    occurrence: {
      id: "occurrence",
      status: "available",
      recordVersion: 2,
      activeCompletionId: null,
    },
  }));

  assert.equal(delayed.confirmedResult, current.confirmedResult);
  assert.equal(getCompletionPresentation("owner", "occurrence")?.canonical.occurrenceVersion, 3);
  assert.equal(getCompletionPresentation("owner", "occurrence")?.canonical.campaignVersion, 5);
});

test("account scope prevents another owner from seeing pending state", async () => {
  await clearCompletionPresentations();
  beginCompletionPresentation("first-owner", quest(), input());
  assert.equal(getCompletionPresentation("second-owner", "occurrence"), null);
});

test("failure is stored before rollback and pending state cannot resurrect", async () => {
  await clearCompletionPresentations();
  beginCompletionPresentation("owner", quest(), input());
  const failure = {
    reason: "stale_version",
    kind: "permanent_failure",
    message: "Changed elsewhere.",
    nextAction: "Review latest state",
    refreshCanonical: true,
  };
  const first = failCompletionPresentation(
    "owner",
    "occurrence",
    "mutation",
    failure,
  );
  const repeated = failCompletionPresentation(
    "owner",
    "occurrence",
    "mutation",
    failure,
  );
  assert.equal(first.changed, true);
  assert.equal(repeated.changed, false);
  assert.equal(first.presentation?.phase, "permanent_failure");
  assert.equal(first.presentation?.canonical.occurrenceStatus, "available");

  refreshCompletionCanonical("owner", quest({
    occurrence: {
      id: "occurrence",
      status: "expired",
      recordVersion: 3,
      activeCompletionId: null,
    },
  }));
  const afterRestartEquivalent = getCompletionPresentation("owner", "occurrence");
  assert.equal(afterRestartEquivalent?.phase, "permanent_failure");
  assert.equal(afterRestartEquivalent?.canonical.occurrenceStatus, "expired");
});
