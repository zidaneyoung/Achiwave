import type { CompleteOccurrenceInput } from "./api";

export const COMPLETION_QUEUE_SCHEMA_VERSION = 1;

export type CompletionQueueState =
  | "pending"
  | "in_flight"
  | "retryable_failure"
  | "succeeded"
  | "permanent_failure"
  | "cancelled";

export interface CompletionQueueRecord {
  queueId: string;
  schemaVersion: number;
  accountId: string;
  deviceId: string;
  operationType: "complete_occurrence";
  occurrenceId: string;
  expectedOccurrenceVersion: number;
  clientMutationId: string;
  canonicalPayloadHash: string;
  deviceObservedAt: string;
  deviceTimezoneName: string;
  state: CompletionQueueState;
  attemptCount: number;
  automaticAttemptCount: number;
  nextAttemptAt: string | null;
  lastAttemptAt: string | null;
  leaseExpiresAt: string | null;
  safeErrorClass: string | null;
  safeErrorMessage: string | null;
  completionId: string | null;
  campaignId: string | null;
  eventSequence: number | null;
  canonicalResultJson: string | null;
  createdAt: string;
  updatedAt: string;
  terminalAt: string | null;
}

export function inputFromQueueRecord(
  record: CompletionQueueRecord,
): CompleteOccurrenceInput {
  return {
    occurrenceId: record.occurrenceId,
    expectedOccurrenceVersion: record.expectedOccurrenceVersion,
    clientMutationId: record.clientMutationId,
    deviceObservedAt: record.deviceObservedAt,
    deviceTimezoneName: record.deviceTimezoneName,
  };
}
