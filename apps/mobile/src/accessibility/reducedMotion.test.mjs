import assert from "node:assert/strict";
import test from "node:test";

import { resolveReducedMotion } from "./reducedMotion.ts";

test("reduced motion resolves explicit and system preferences", () => {
  assert.equal(resolveReducedMotion("reduce", false), true);
  assert.equal(resolveReducedMotion("allow", true), false);
  assert.equal(resolveReducedMotion("system", true), true);
  assert.equal(resolveReducedMotion("system", false), false);
});
