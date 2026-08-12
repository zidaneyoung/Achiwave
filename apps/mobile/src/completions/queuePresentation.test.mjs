import assert from "node:assert/strict";
import test from "node:test";

import {
  completionQueueStatePresentation,
  isCompletionQueueRecordRelevant,
} from "./queuePresentation.ts";

test("all queue lifecycle states have distinct text and non-colour action cues", () => {
  const states = [
    "pending",
    "in_flight",
    "succeeded",
    "retryable_failure",
    "permanent_failure",
    "cancelled",
  ];
  const presentations = states.map(completionQueueStatePresentation);
  assert.equal(new Set(presentations.map(({ label }) => label)).size, states.length);
  assert.equal(presentations[3].action, "retry");
  assert.equal(presentations[4].action, "dismiss_and_refresh");
  assert.equal(presentations[5].action, null);
  assert.ok(presentations.every(({ announcement, label }) => announcement && label));
});

test("a retained success stops controlling UI after a later reversal", () => {
  const succeeded = { state: "succeeded", completionId: "completion-1" };
  assert.equal(isCompletionQueueRecordRelevant(succeeded, "completion-1"), true);
  assert.equal(isCompletionQueueRecordRelevant(succeeded, null), false);
  assert.equal(
    isCompletionQueueRecordRelevant(
      { state: "permanent_failure", completionId: null },
      null,
    ),
    true,
  );
});
