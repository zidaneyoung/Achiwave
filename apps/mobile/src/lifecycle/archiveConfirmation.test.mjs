import assert from "node:assert/strict";
import test from "node:test";

import {
  campaignArchiveConfirmation,
  questArchiveConfirmation,
} from "./archiveConfirmation.ts";

test("campaign archive confirmation names the campaign and explains reversible effects", () => {
  const copy = campaignArchiveConfirmation("Marathon training");

  assert.equal(copy.title, "Archive \"Marathon training\"?");
  assert.match(copy.description, /hidden from current views/i);
  assert.match(copy.description, /new quests, recurrence generation, and quest completion will be blocked/i);
  assert.match(copy.description, /existing quests, occurrences, completions, rewards, reversals, and audit history will be preserved/i);
  assert.match(copy.description, /restore the campaign later/i);
  assert.doesNotMatch(`${copy.title} ${copy.description}`, /delete|permanent/i);
});

test("quest archive confirmation names the quest and explains reversible effects", () => {
  const copy = questArchiveConfirmation("Morning run");

  assert.equal(copy.title, "Archive \"Morning run\"?");
  assert.match(copy.description, /hidden from current views/i);
  assert.match(copy.description, /new occurrences and quest completion will be blocked/i);
  assert.match(copy.description, /existing occurrences, completions, rewards, reversals, and audit history will be preserved/i);
  assert.match(copy.description, /restore the quest later/i);
  assert.doesNotMatch(`${copy.title} ${copy.description}`, /delete|permanent/i);
});
