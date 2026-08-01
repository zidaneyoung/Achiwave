import assert from "node:assert/strict";
import test from "node:test";

import { DARK_COLORS, LIGHT_COLORS } from "./colors.ts";
import { contrastRatio } from "./contrast.ts";

const palettes = { dark: DARK_COLORS, light: LIGHT_COLORS };

for (const [name, colors] of Object.entries(palettes)) {
  test(`${name} theme meets normal-text contrast`, () => {
    const pairs = [
      ["foreground/background", colors.foreground, colors.background],
      ["foreground/surface", colors.foreground, colors.surface],
      ["muted/background", colors.foregroundMuted, colors.background],
      ["muted/surface", colors.foregroundMuted, colors.surface],
      ["action", colors.onAction, colors.action],
      ["danger", colors.onAction, colors.danger],
      ["success", colors.success, colors.background],
      ["warning", colors.warning, colors.background],
      ["error", colors.error, colors.background],
      ["info", colors.info, colors.background],
    ];
    for (const [label, foreground, background] of pairs) {
      assert.ok(
        contrastRatio(foreground, background) >= 4.5,
        `${label} must meet 4.5:1`,
      );
    }
  });

  test(`${name} theme focus indicator remains visible`, () => {
    assert.ok(contrastRatio(colors.focus, colors.background) >= 3);
    assert.ok(contrastRatio(colors.focus, colors.surface) >= 3);
  });
}
