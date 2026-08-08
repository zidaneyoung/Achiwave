import assert from "node:assert/strict";
import test from "node:test";

import { validateOneTimeQuestForm } from "./form.ts";

test("one-time quest form trims title and parses whole XP", () => {
  assert.deepEqual(validateOneTimeQuestForm("  Write brief  ", "20", "  Context  "), {
    title: "Write brief", rewardXp: 20, description: "Context",
    dueLocalDateTime: null,
    titleError: null, rewardError: null, descriptionError: null, dueError: null,
  });
});

test("one-time quest form validates local due intent without using the device clock", () => {
  const valid = validateOneTimeQuestForm("Quest", "0", "", "2099-12-31T23:00");
  assert.equal(valid.dueLocalDateTime, "2099-12-31T23:00");
  assert.equal(valid.dueError, null);
  assert.ok(validateOneTimeQuestForm("Quest", "0", "", "2099-02-30T09:00").dueError);
  assert.ok(validateOneTimeQuestForm("Quest", "0", "", "December 31").dueError);
});

test("one-time quest form rejects blank title and invalid XP", () => {
  const result = validateOneTimeQuestForm(" ", "1.5");
  assert.ok(result.titleError);
  assert.ok(result.rewardError);
});

test("one-time quest form preserves absent description and rejects unsafe content", () => {
  assert.equal(validateOneTimeQuestForm("Quest", "0", " ").description, null);
  assert.ok(validateOneTimeQuestForm("Quest", "0", "unsafe\u0000").descriptionError);
});
