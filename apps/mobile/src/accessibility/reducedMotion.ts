import type { ReducedMotionPreference } from "../preferences/types";

const listeners = new Set<(preference: ReducedMotionPreference) => void>();

export function resolveReducedMotion(
  preference: ReducedMotionPreference,
  systemReduceMotion: boolean,
): boolean {
  if (preference === "reduce") return true;
  if (preference === "allow") return false;
  return systemReduceMotion;
}

export function publishReducedMotionPreference(preference: ReducedMotionPreference) {
  for (const listener of listeners) listener(preference);
}

export function subscribeReducedMotionPreference(
  listener: (preference: ReducedMotionPreference) => void,
) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
