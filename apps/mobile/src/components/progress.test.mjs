import assert from "node:assert/strict";
import test from "node:test";

import { clampProgress } from "./progress.ts";

test("progress values clamp safely", () => {
  assert.equal(clampProgress(-1), 0);
  assert.equal(clampProgress(42), 42);
  assert.equal(clampProgress(120), 100);
  assert.equal(clampProgress(Number.NaN), 0);
});
