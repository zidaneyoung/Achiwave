import assert from "node:assert/strict";
import test from "node:test";

import {
  buildQuestListPath,
  countQuestListFilters,
  createEmptyQuestListFilters,
  validateQuestListDates,
} from "./list.ts";

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
