import * as SecureStore from "expo-secure-store";

import { getRuntimeEnvironment } from "../config/runtime";
import type { PreferenceSnapshot } from "./types";

const CACHE_VERSION = 1;
const cacheKey = `achiwave.${getRuntimeEnvironment().apiEnvironment}.presentation-preferences`;

interface StoredPreferenceSnapshot extends PreferenceSnapshot {
  cacheVersion: typeof CACHE_VERSION;
}

function isStoredSnapshot(value: unknown): value is StoredPreferenceSnapshot {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    candidate.cacheVersion === CACHE_VERSION &&
    typeof candidate.timezoneName === "string" &&
    typeof candidate.timezoneVersion === "number" &&
    typeof candidate.timezoneEffectiveAt === "string" &&
    (candidate.notificationPreference === "unspecified" ||
      candidate.notificationPreference === "enabled" ||
      candidate.notificationPreference === "disabled") &&
    (candidate.dateFormat === "system" ||
      candidate.dateFormat === "day_month_year" ||
      candidate.dateFormat === "month_day_year" ||
      candidate.dateFormat === "year_month_day") &&
    typeof candidate.soundEnabled === "boolean" &&
    typeof candidate.hapticsEnabled === "boolean" &&
    (candidate.reducedMotion === "system" ||
      candidate.reducedMotion === "reduce" ||
      candidate.reducedMotion === "allow") &&
    typeof candidate.recordVersion === "number"
  );
}

export async function saveCachedPreferences(
  preferences: PreferenceSnapshot,
): Promise<void> {
  const stored: StoredPreferenceSnapshot = {
    cacheVersion: CACHE_VERSION,
    ...preferences,
  };
  await SecureStore.setItemAsync(cacheKey, JSON.stringify(stored));
}

export async function loadCachedPreferences(): Promise<PreferenceSnapshot | null> {
  const serialized = await SecureStore.getItemAsync(cacheKey);
  if (serialized === null) {
    return null;
  }
  try {
    const parsed: unknown = JSON.parse(serialized);
    if (!isStoredSnapshot(parsed)) {
      throw new Error("Invalid preference cache.");
    }
    const { cacheVersion: _cacheVersion, ...preferences } = parsed;
    return preferences;
  } catch {
    await SecureStore.deleteItemAsync(cacheKey);
    return null;
  }
}

export async function clearCachedPreferences(): Promise<void> {
  await SecureStore.deleteItemAsync(cacheKey);
}
