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
