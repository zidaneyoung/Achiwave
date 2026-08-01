import assert from "node:assert/strict";
import test from "node:test";

import { ROOT_DESTINATIONS } from "./rootDestinations.ts";
import {
  AUTHENTICATED_TAB_BACK_BEHAVIOR,
  AUTHENTICATED_TAB_INITIAL_ROUTE,
} from "./backBehavior.ts";
import { DETAIL_COPY, isRootDestination, PROTECTED_ROUTES } from "./routes.ts";

test("root destinations remain unique and complete", () => {
  const names = ROOT_DESTINATIONS.map(({ name }) => name);
  assert.deepEqual(names, ["home", "campaigns", "progress", "profile"]);
  assert.equal(new Set(names).size, names.length);
});

test("detail routes accept only permitted root destinations", () => {
  for (const destination of ROOT_DESTINATIONS) {
    assert.equal(isRootDestination(destination.name), true);
    assert.equal(PROTECTED_ROUTES.detail(destination.name).params.section, destination.name);
    assert.ok(DETAIL_COPY[destination.name].title);
  }
  assert.equal(isRootDestination("quests"), false);
  assert.equal(isRootDestination(["home"]), false);
  assert.equal(isRootDestination(undefined), false);
});

test("modal route remains an explicit protected temporary surface", () => {
  assert.equal(PROTECTED_ROUTES.modal, "/(protected)/modal");
});

test("Android back uses native stacks and bounded tab history", () => {
  assert.equal(AUTHENTICATED_TAB_BACK_BEHAVIOR, "history");
  assert.equal(AUTHENTICATED_TAB_INITIAL_ROUTE, "home");
});
