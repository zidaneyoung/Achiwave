import assert from "node:assert/strict";
import test from "node:test";

import {
  createQuestFormSnapshot,
  questFormSnapshotsEqual,
} from "../forms/snapshots.ts";

test("quest create defaults are clean and every committed planning choice is compared", () => {
  const initial = createQuestFormSnapshot({
    title: "",
    description: "",
    category: null,
    difficulty: "medium",
    reward: "0",
    committedDue: "",
  });
  const whitespaceOnly = createQuestFormSnapshot({
    title: "  ",
    description: "  ",
    category: null,
    difficulty: "medium",
    reward: " 0 ",
    committedDue: null,
  });

  assert.equal(questFormSnapshotsEqual(initial, whitespaceOnly), true);
  for (const changed of [
    { ...initial, title: "Plan" },
    { ...initial, description: "Context" },
    { ...initial, category: "work" },
    { ...initial, difficulty: "hard" },
    { ...initial, reward: "10" },
    { ...initial, committedDue: "2027-03-14T09:30" },
    { ...initial, title: "Invalid\u0000" },
  ]) {
    assert.equal(questFormSnapshotsEqual(initial, changed), false);
  }
});

test("quest edit snapshots preserve the canonical initial baseline", () => {
  const initial = createQuestFormSnapshot({
    title: "  Ship release  ",
    description: " Notes ",
    category: "work",
    difficulty: "hard",
    reward: "20",
    committedDue: "2027-03-14T09:30",
  });

  assert.deepEqual(initial, {
    title: "Ship release",
    description: "Notes",
    category: "work",
    difficulty: "hard",
    reward: "20",
    committedDue: "2027-03-14T09:30",
  });
});
