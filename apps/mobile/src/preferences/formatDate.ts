import type { DateFormatPreference } from "./types";

export function formatPreferenceDate(
  date: Date,
  preference: DateFormatPreference,
): string {
  if (preference === "system") {
    return date.toLocaleDateString();
  }
  const components = new Intl.DateTimeFormat(undefined, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  })
    .formatToParts(date)
    .reduce<Record<string, string>>((result, part) => {
      if (part.type === "day" || part.type === "month" || part.type === "year") {
        result[part.type] = part.value;
      }
      return result;
    }, {});
  const day = components.day ?? "";
  const month = components.month ?? "";
  const year = components.year ?? "";
  if (preference === "day_month_year") {
    return `${day}/${month}/${year}`;
  }
  if (preference === "month_day_year") {
    return `${month}/${day}/${year}`;
  }
  return `${year}-${month}-${day}`;
}

export function formatPreferenceDateTime(
  date: Date,
  preference: DateFormatPreference,
  timeZone: string,
): string {
  const safeTimeZone = (() => {
    try {
      new Intl.DateTimeFormat(undefined, { timeZone }).format(date);
      return timeZone;
    } catch {
      return "UTC";
    }
  })();
  const parts = new Intl.DateTimeFormat(undefined, {
    day: preference === "system" ? "numeric" : "2-digit",
    hour: "numeric",
    minute: "2-digit",
    month: preference === "system" ? "numeric" : "2-digit",
    timeZone: safeTimeZone,
    year: "numeric",
  }).formatToParts(date);
  const values = parts.reduce<Record<string, string>>((result, part) => {
    if (["day", "month", "year", "hour", "minute", "dayPeriod"].includes(part.type)) {
      result[part.type] = part.value;
    }
    return result;
  }, {});
  const dateValue =
    preference === "day_month_year"
      ? `${values.day}/${values.month}/${values.year}`
      : preference === "month_day_year"
        ? `${values.month}/${values.day}/${values.year}`
        : preference === "year_month_day"
          ? `${values.year}-${values.month}-${values.day}`
          : new Intl.DateTimeFormat(undefined, {
              day: "numeric",
              month: "numeric",
              timeZone: safeTimeZone,
              year: "numeric",
            }).format(date);
  const timeValue = `${values.hour}:${values.minute}${values.dayPeriod ? ` ${values.dayPeriod}` : ""}`;
  return `${dateValue} ${timeValue}`;
}
