export const COMPLETION_RETRY_INITIAL_MILLISECONDS = 5_000;
export const COMPLETION_RETRY_MAX_MILLISECONDS = 15 * 60 * 1_000;
export const COMPLETION_RETRY_MAX_AUTOMATIC_ATTEMPTS = 8;

export interface RetryScheduleSource {
  now(): Date;
  random(): number;
}

const defaultSource: RetryScheduleSource = {
  now: () => new Date(),
  random: () => Math.random(),
};

export function parseRetryAfterMilliseconds(
  value: string | null,
  nowMilliseconds = Date.now(),
): number | null {
  if (value === null) return null;
  const seconds = Number(value);
  if (Number.isFinite(seconds) && seconds >= 0) return seconds * 1_000;
  const date = Date.parse(value);
  return Number.isFinite(date) ? Math.max(0, date - nowMilliseconds) : null;
}

export function nextCompletionRetryAt(
  automaticAttemptCount: number,
  serverRetryAfterMilliseconds: number | null,
  source: RetryScheduleSource = defaultSource,
): string | null {
  if (
    automaticAttemptCount < 1 ||
    automaticAttemptCount >= COMPLETION_RETRY_MAX_AUTOMATIC_ATTEMPTS
  ) return null;
  const exponential = Math.min(
    COMPLETION_RETRY_INITIAL_MILLISECONDS * 2 ** (automaticAttemptCount - 1),
    COMPLETION_RETRY_MAX_MILLISECONDS,
  );
  const safeRandom = Math.max(0, Math.min(1, source.random()));
  const jittered = Math.min(
    exponential + Math.floor(exponential * 0.2 * safeRandom),
    COMPLETION_RETRY_MAX_MILLISECONDS,
  );
  const delay = Math.max(jittered, serverRetryAfterMilliseconds ?? 0);
  return new Date(source.now().getTime() + delay).toISOString();
}
