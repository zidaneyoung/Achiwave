const LOCAL_DATE_TIME_PATTERN = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/u;

interface LocalDateTimeParts {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
}

function parseLocalDateTime(value: string): LocalDateTimeParts | null {
  const match = LOCAL_DATE_TIME_PATTERN.exec(value);
  if (!match) return null;
  const [, year, month, day, hour, minute] = match;
  const parts = {
    year: Number(year),
    month: Number(month),
    day: Number(day),
    hour: Number(hour),
    minute: Number(minute),
  };
  const candidate = new Date(
    Date.UTC(parts.year, parts.month - 1, parts.day, parts.hour, parts.minute),
  );
  if (
    candidate.getUTCFullYear() !== parts.year ||
    candidate.getUTCMonth() !== parts.month - 1 ||
    candidate.getUTCDate() !== parts.day ||
    candidate.getUTCHours() !== parts.hour ||
    candidate.getUTCMinutes() !== parts.minute
  ) {
    return null;
  }
  return parts;
}

function formatLocalDateTime(parts: LocalDateTimeParts): string {
  const twoDigits = (value: number) => String(value).padStart(2, "0");
  return `${String(parts.year).padStart(4, "0")}-${twoDigits(parts.month)}-${twoDigits(parts.day)}T${twoDigits(parts.hour)}:${twoDigits(parts.minute)}`;
}

function getZonedParts(date: Date, timeZoneName: string): LocalDateTimeParts {
  const values = new Intl.DateTimeFormat("en-CA", {
    calendar: "gregory",
    day: "2-digit",
    hour: "2-digit",
    hourCycle: "h23",
    minute: "2-digit",
    month: "2-digit",
    numberingSystem: "latn",
    timeZone: timeZoneName,
    year: "numeric",
  })
    .formatToParts(date)
    .reduce<Record<string, string>>((result, part) => {
      if (["year", "month", "day", "hour", "minute"].includes(part.type)) {
        result[part.type] = part.value;
      }
      return result;
    }, {});
  return {
    year: Number(values.year),
    month: Number(values.month),
    day: Number(values.day),
    hour: Number(values.hour),
    minute: Number(values.minute),
  };
}

function partsAsUtcMilliseconds(parts: LocalDateTimeParts): number {
  return Date.UTC(parts.year, parts.month - 1, parts.day, parts.hour, parts.minute);
}

function partsMatch(left: LocalDateTimeParts, right: LocalDateTimeParts): boolean {
  return (
    left.year === right.year &&
    left.month === right.month &&
    left.day === right.day &&
    left.hour === right.hour &&
    left.minute === right.minute
  );
}

export function isSupportedTimeZone(timeZoneName: string | null): timeZoneName is string {
  if (!timeZoneName) return false;
  try {
    new Intl.DateTimeFormat("en", { timeZone: timeZoneName }).format(new Date(0));
    return true;
  } catch {
    return false;
  }
}

export function pickerValueForLocalDateTime(
  value: string,
  timeZoneName: string,
  fallback: Date,
): Date {
  const target = parseLocalDateTime(value);
  if (!target || !isSupportedTimeZone(timeZoneName)) return fallback;

  let timestamp = partsAsUtcMilliseconds(target);
  for (let attempt = 0; attempt < 4; attempt += 1) {
    const actual = getZonedParts(new Date(timestamp), timeZoneName);
    const adjustment = partsAsUtcMilliseconds(target) - partsAsUtcMilliseconds(actual);
    if (adjustment === 0) return new Date(timestamp);
    timestamp += adjustment;
  }

  const candidate = new Date(timestamp);
  return partsMatch(getZonedParts(candidate, timeZoneName), target) ? candidate : fallback;
}

export function commitQuestDueDateTimeSelection(
  currentValue: string,
  selectedDate: Date | null,
  selectedTime: Date | null,
  timeZoneName: string,
): string {
  if (!selectedDate || !selectedTime) return currentValue;
  const dateParts = getZonedParts(selectedDate, timeZoneName);
  const timeParts = getZonedParts(selectedTime, timeZoneName);
  return formatLocalDateTime({
    ...dateParts,
    hour: timeParts.hour,
    minute: timeParts.minute,
  });
}

export function formatQuestDueDateTimeValue(
  value: string,
  timeZoneName: string,
  locale?: string,
): string {
  const parts = parseLocalDateTime(value);
  if (!parts) return value;
  const wallTime = new Date(partsAsUtcMilliseconds(parts));
  const formatted = new Intl.DateTimeFormat(locale, {
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    month: "short",
    timeZone: "UTC",
    year: "numeric",
  }).format(wallTime);
  return `${formatted} (${timeZoneName})`;
}
