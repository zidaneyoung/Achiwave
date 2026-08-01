import assert from "node:assert/strict";
import test from "node:test";

import { sizing, spacing, supportedFontScales, supportedViewports, typography } from "./tokens.ts";

test("spacing follows the documented four-point unit", () => {
  for (const value of Object.values(spacing)) {
    assert.equal(value % 4, 0);
  }
});

test("semantic typography preserves the required scale", () => {
  assert.deepEqual(
    Object.values(typography).map(({ fontSize, lineHeight }) => [fontSize, lineHeight]),
    [[32, 38], [28, 34], [22, 28], [18, 24], [16, 24], [14, 20], [12, 16]],
  );
});

test("compact viewport and touch dimensions remain explicit", () => {
  assert.equal(sizing.compactViewportWidth, 320);
  assert.equal(sizing.compactViewportHeight, 568);
  assert.equal(sizing.minimumTouchTarget, 48);
});

test("large-text and viewport acceptance matrices remain explicit", () => {
  assert.deepEqual(supportedFontScales, [1, 1.3, 1.5, 2]);
  assert.deepEqual(supportedViewports[0], { width: 320, height: 568 });
});
