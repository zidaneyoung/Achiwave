import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
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

test("pending campaign and quest submissions lock dirty-form dismissal", async () => {
  const dialogSource = await readFile(
    new URL("./useDirtyFormGuard.tsx", import.meta.url),
    "utf8",
  );
  assert.match(dialogSource, /busy\?: boolean;/u);
  assert.match(dialogSource, /<AppDialog\s+busy=\{busy\}/u);

  const formSources = await Promise.all([
    "../../app/(protected)/campaigns/new.tsx",
    "../../app/(protected)/campaigns/[campaignId]/edit.tsx",
    "../../app/(protected)/campaigns/[campaignId]/quests/new.tsx",
    "../../app/(protected)/quests/[questId]/edit.tsx",
  ].map((path) => readFile(new URL(path, import.meta.url), "utf8")));

  for (const source of formSources) {
    assert.match(
      source,
      /<DirtyFormDialog busy=\{submitting\} guard=\{guard\} \/>/u,
    );
  }
});
