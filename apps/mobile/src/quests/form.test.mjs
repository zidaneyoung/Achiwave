import assert from "node:assert/strict";
import test from "node:test";

import { validateOneTimeQuestForm } from "./form.ts";

test("one-time quest form trims title and parses whole XP", () => {
  assert.deepEqual(validateOneTimeQuestForm("  Write brief  ", "20"), {
    title: "Write brief", rewardXp: 20, titleError: null, rewardError: null,
  });
});

test("one-time quest form rejects blank title and invalid XP", () => {
  const result = validateOneTimeQuestForm(" ", "1.5");
  assert.ok(result.titleError);
  assert.ok(result.rewardError);
});
