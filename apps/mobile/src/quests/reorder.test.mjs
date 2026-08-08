import assert from "node:assert/strict";
import test from "node:test";

import { applyQuestOrder, moveQuest } from "./reorder.ts";

test("move quest changes one adjacent position and rejects boundaries", () => {
  const quests = [{ id: "a" }, { id: "b" }, { id: "c" }];
  assert.deepEqual(moveQuest(quests, 1, "up")?.map((quest) => quest.id), ["b", "a", "c"]);
  assert.deepEqual(moveQuest(quests, 1, "down")?.map((quest) => quest.id), ["a", "c", "b"]);
  assert.equal(moveQuest(quests, 0, "up"), null);
  assert.equal(moveQuest(quests, 2, "down"), null);
  assert.deepEqual(quests.map((quest) => quest.id), ["a", "b", "c"]);
});

test("canonical order updates active quests without dropping archived history", () => {
  const detail = {
    id: "campaign",
    recordVersion: 4,
    quests: [
      { id: "a", definitionState: "active", displayOrder: 0, recordVersion: 1 },
      { id: "b", definitionState: "active", displayOrder: 1, recordVersion: 1 },
      { id: "history", definitionState: "archived", displayOrder: 0, recordVersion: 2 },
    ],
  };
  const result = applyQuestOrder(detail, {
    campaignId: "campaign",
    campaignRecordVersion: 5,
    items: [
      { id: "b", displayOrder: 0, recordVersion: 2 },
      { id: "a", displayOrder: 1, recordVersion: 2 },
    ],
  });
  assert.equal(result.recordVersion, 5);
  assert.deepEqual(result.quests.map((quest) => quest.id), ["b", "a", "history"]);
  assert.equal(result.quests[2].recordVersion, 2);
});
