import assert from "node:assert/strict";
import test from "node:test";

import { sizing, spacing } from "../theme/tokens.ts";

test("interactive target helpers enforce the 48 dp baseline", () => {
  assert.equal(sizing.minimumTouchTarget, 48);
  assert.equal(spacing.xs, 8);
});
