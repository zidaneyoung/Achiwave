import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { resolveSystemBarAppearance } from "./systemBars.ts";

test("system bars remain legible in light and dark appearances", () => {
  assert.deepEqual(resolveSystemBarAppearance("light"), {
    statusBarStyle: "dark-content",
    navigationButtonStyle: "dark",
  });
  assert.deepEqual(resolveSystemBarAppearance("dark"), {
    statusBarStyle: "light-content",
    navigationButtonStyle: "light",
  });
  assert.deepEqual(resolveSystemBarAppearance(null), {
    statusBarStyle: "light-content",
    navigationButtonStyle: "light",
  });
});

test("Android uses native resize for keyboard avoidance", async () => {
  const config = JSON.parse(
    await readFile(new URL("../../app.json", import.meta.url), "utf8"),
  );
  assert.equal(config.expo.android.softwareKeyboardLayoutMode, "resize");
});
