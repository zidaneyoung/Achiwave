import assert from "node:assert/strict";
import test from "node:test";

import { createAndroidRipple } from "./touchFeedback.ts";

test("Android ripple configuration is immediate and bounded by default", () => {
  assert.deepEqual(createAndroidRipple("#123456"), {
    borderless: false,
    color: "#123456",
    foreground: true,
  });
});
