import assert from "node:assert/strict";
import test from "node:test";

import {
  buildQuestListPath,
  combineQuestListPages,
  countQuestListFilters,
  createEmptyQuestListFilters,
  validateQuestListDates,
} from "./list.ts";

test("quest list refresh combines loaded pages and drops removed items", () => {
  const previouslyLoadedIds = ["one", "two", "three", "four"];
  const combined = combineQuestListPages([
    {
      items: [{ id: "one" }, { id: "three" }],
      offset: 0,
      total: 3,
    },
    {
      items: [{ id: "four" }],
      offset: 2,
      total: 3,
    },
  ]);

  assert.deepEqual(combined, {
    items: [{ id: "one" }, { id: "three" }, { id: "four" }],
    nextOffset: 3,
    total: 3,
  });
  assert.equal(previouslyLoadedIds.includes("two"), true);
  assert.equal(combined.items.some((item) => item.id === "two"), false);
});

test("quest list refresh rejects a pagination gap", () => {
  assert.throws(
    () => combineQuestListPages([
      { items: [{ id: "one" }], offset: 0, total: 2 },
      { items: [{ id: "two" }], offset: 2, total: 2 },
    ]),
    /must be contiguous/u,
  );
});

test("quest list query encodes only selected server filters in canonical order", () => {
  assert.equal(
    buildQuestListPath({
      campaignId: "campaign/one",
      status: "available",
      category: "uncategorized",
      dueFrom: " 2026-08-01 ",
      dueTo: "2026-08-31",
    }, 25, 50),
    "/api/v1/quests?campaign_id=campaign%2Fone&status=available&category=uncategorized&due_from=2026-08-01&due_to=2026-08-31&limit=25&offset=50",
  );
  assert.equal(
    buildQuestListPath(createEmptyQuestListFilters()),
    "/api/v1/quests?limit=50&offset=0",
  );
  assert.throws(
    () => buildQuestListPath(createEmptyQuestListFilters(), 0, 0),
    /positive limit/u,
  );
});

test("quest list date validation rejects malformed ranges without device time", () => {
  assert.deepEqual(
    validateQuestListDates({ dueFrom: "2028-02-29", dueTo: "2028-03-01" }),
    { dueFrom: null, dueTo: null },
  );
  assert.match(
    validateQuestListDates({ dueFrom: "2027-02-29", dueTo: "" }).dueFrom ?? "",
    /YYYY-MM-DD/u,
  );
  assert.match(
    validateQuestListDates({ dueFrom: "2026-08-31", dueTo: "2026-08-01" }).dueTo ?? "",
    /on or after/u,
  );
});

test("active filter count treats blank date text as unset", () => {
  assert.equal(countQuestListFilters(createEmptyQuestListFilters()), 0);
  assert.equal(countQuestListFilters({
    campaignId: "campaign",
    status: "completed",
    category: null,
    dueFrom: "  ",
    dueTo: "2026-08-31",
  }), 3);
});
