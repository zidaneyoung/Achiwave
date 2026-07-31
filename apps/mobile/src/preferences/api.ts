import { authenticationService } from "../auth/service";
import { loadCachedPreferences, saveCachedPreferences } from "./cache";
import type { DateFormatPreference, PreferenceSnapshot } from "./types";

export class PreferenceRequestError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PreferenceRequestError";
  }
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isDateFormat(value: unknown): value is DateFormatPreference {
  return (
    value === "system" ||
    value === "day_month_year" ||
    value === "month_day_year" ||
    value === "year_month_day"
  );
}

function parsePreferences(value: unknown): PreferenceSnapshot | null {
  if (!isObject(value)) {
    return null;
  }
  const notificationPreference = value.notification_preference;
  if (
    typeof value.timezone_name !== "string" ||
    typeof value.timezone_version !== "number" ||
    typeof value.timezone_effective_at !== "string" ||
    (notificationPreference !== "unspecified" &&
      notificationPreference !== "enabled" &&
      notificationPreference !== "disabled") ||
    !isDateFormat(value.date_format) ||
    typeof value.sound_enabled !== "boolean" ||
    typeof value.haptics_enabled !== "boolean" ||
    typeof value.record_version !== "number"
  ) {
    return null;
  }
  return {
    timezoneName: value.timezone_name,
    timezoneVersion: value.timezone_version,
    timezoneEffectiveAt: value.timezone_effective_at,
    notificationPreference,
    dateFormat: value.date_format,
    soundEnabled: value.sound_enabled,
    hapticsEnabled: value.haptics_enabled,
    recordVersion: value.record_version,
  };
}

async function parseResponse(response: Response): Promise<PreferenceSnapshot> {
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new PreferenceRequestError("Preferences are temporarily unavailable.");
  }
  if (!response.ok) {
    if (isObject(body) && body.code === "stale_record_version") {
      throw new PreferenceRequestError(
        "Preferences changed elsewhere. Refresh before trying again.",
      );
    }
    throw new PreferenceRequestError("Preferences could not be updated.");
  }
  const preferences = parsePreferences(body);
  if (!preferences) {
    throw new PreferenceRequestError("Preferences are temporarily unavailable.");
  }
  try {
    await saveCachedPreferences(preferences);
  } catch {
    // A non-authoritative presentation cache must never fail the server update.
  }
  return preferences;
}

interface PresentationPreferenceUpdates {
  dateFormat?: DateFormatPreference;
  soundEnabled?: boolean;
  hapticsEnabled?: boolean;
}

async function updatePresentation(
  updates: PresentationPreferenceUpdates,
  recordVersion: number,
): Promise<PreferenceSnapshot> {
  const response = await authenticationService.request("/api/v1/preferences", {
    body: JSON.stringify({
      ...(updates.dateFormat === undefined
        ? {}
        : { date_format: updates.dateFormat }),
      ...(updates.soundEnabled === undefined
        ? {}
        : { sound_enabled: updates.soundEnabled }),
      ...(updates.hapticsEnabled === undefined
        ? {}
        : { haptics_enabled: updates.hapticsEnabled }),
      record_version: recordVersion,
    }),
    headers: { "Content-Type": "application/json" },
    method: "PATCH",
  });
  return parseResponse(response);
}

export const preferenceApi = {
  async get(): Promise<PreferenceSnapshot> {
    const response = await authenticationService.request("/api/v1/preferences");
    return parseResponse(response);
  },

  async updateDateFormat(
    dateFormat: DateFormatPreference,
    recordVersion: number,
  ): Promise<PreferenceSnapshot> {
    return updatePresentation({ dateFormat }, recordVersion);
  },

  async updateFeedback(
    updates: { soundEnabled?: boolean; hapticsEnabled?: boolean },
    recordVersion: number,
  ): Promise<PreferenceSnapshot> {
    return updatePresentation(updates, recordVersion);
  },

  getCached(): Promise<PreferenceSnapshot | null> {
    return loadCachedPreferences();
  },
};
