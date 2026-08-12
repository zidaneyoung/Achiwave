import type { CompleteOccurrenceInput } from "./api";
import type { CompletionQueueRecord } from "./queueTypes";

export const NON_TERMINAL_QUEUE_STATES = [
  "pending",
  "in_flight",
  "retryable_failure",
] as const;

export function canonicalCompletionPayload(
  input: CompleteOccurrenceInput,
): string {
  return JSON.stringify({
    device_observed_at: input.deviceObservedAt,
    device_timezone_name: input.deviceTimezoneName,
    expected_occurrence_version: input.expectedOccurrenceVersion,
    occurrence_id: input.occurrenceId,
  });
}

export function activeQueueRecord(
  records: CompletionQueueRecord[],
  accountId: string,
  occurrenceId: string,
): CompletionQueueRecord | null {
  return records.find(
    (record) =>
      record.accountId === accountId &&
      record.occurrenceId === occurrenceId &&
      NON_TERMINAL_QUEUE_STATES.includes(
        record.state as (typeof NON_TERMINAL_QUEUE_STATES)[number],
      ),
  ) ?? null;
}
