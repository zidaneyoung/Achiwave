import assert from "node:assert/strict";
import test from "node:test";

import {
  createDirtyFormGuardState,
  reduceDirtyFormGuard,
  shouldPreventDirtyFormRemoval,
} from "./dirtyFormGuard.ts";

test("guard queues only the first intercepted removal action", () => {
  const first = { type: "GO_BACK", source: "first" };
  const second = { type: "POP", source: "second" };
  const prompting = reduceDirtyFormGuard(createDirtyFormGuardState(), {
    type: "intercept",
    action: first,
  });

  assert.deepEqual(
    reduceDirtyFormGuard(prompting, { type: "intercept", action: second }),
    prompting,
  );
  assert.equal(shouldPreventDirtyFormRemoval(true, prompting), true);
});

test("stay clears the pending action while keeping removal prevention enabled", () => {
  const prompting = reduceDirtyFormGuard(createDirtyFormGuardState(), {
    type: "intercept",
    action: { type: "GO_BACK" },
  });
  const stayed = reduceDirtyFormGuard(prompting, { type: "stay" });

  assert.deepEqual(stayed, createDirtyFormGuardState());
  assert.equal(shouldPreventDirtyFormRemoval(true, stayed), true);
});

test("discard and committed success disable prevention before navigation", () => {
  const prompting = reduceDirtyFormGuard(createDirtyFormGuardState(), {
    type: "intercept",
    action: { type: "GO_BACK" },
  });
  const discarding = reduceDirtyFormGuard(prompting, { type: "discard" });
  const committing = reduceDirtyFormGuard(prompting, { type: "commit" });

  assert.deepEqual(discarding, { phase: "dispatching", action: { type: "GO_BACK" } });
  assert.equal(shouldPreventDirtyFormRemoval(true, discarding), false);
  assert.deepEqual(committing, { phase: "committing", action: null });
  assert.equal(shouldPreventDirtyFormRemoval(true, committing), false);
});
