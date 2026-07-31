export type DateFormatPreference =
  | "system"
  | "day_month_year"
  | "month_day_year"
  | "year_month_day";

export interface PreferenceSnapshot {
  timezoneName: string;
  timezoneVersion: number;
  timezoneEffectiveAt: string;
  notificationPreference: "unspecified" | "enabled" | "disabled";
  dateFormat: DateFormatPreference;
  recordVersion: number;
}
