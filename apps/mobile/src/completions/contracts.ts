import type {
  CompleteOccurrenceResult,
  CompletionCampaign,
  CompletionOccurrence,
  CompletionRecord,
  ProgressEventReference,
  ReverseCompletionResult,
} from "./types";

export function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function positiveInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 1;
}

function nullableString(value: unknown): string | null | undefined {
  if (value === null) return null;
  return typeof value === "string" ? value : undefined;
}

function parseOccurrence(value: unknown): CompletionOccurrence | null {
  if (!isObject(value)) return null;
  const completedAt = nullableString(value.completed_at);
  const reversedAt = nullableString(value.reversed_at);
  if (
    typeof value.id !== "string" ||
    typeof value.quest_id !== "string" ||
    typeof value.campaign_id !== "string" ||
    (value.status !== "scheduled" && value.status !== "available" &&
      value.status !== "completed" && value.status !== "reversed" &&
      value.status !== "expired" && value.status !== "voided") ||
    !positiveInteger(value.record_version) ||
    completedAt === undefined ||
    reversedAt === undefined
  ) return null;
  return {
    id: value.id,
    questId: value.quest_id,
    campaignId: value.campaign_id,
    status: value.status,
    recordVersion: value.record_version,
    completedAt,
    reversedAt,
  };
}

function parseCompletion(value: unknown): CompletionRecord | null {
  if (!isObject(value)) return null;
  const reversedAt = nullableString(value.reversed_at);
  const deviceObservedAt = nullableString(value.device_observed_at);
  const deviceTimezoneName = nullableString(value.device_timezone_name);
  if (
    typeof value.id !== "string" ||
    typeof value.occurrence_id !== "string" ||
    typeof value.server_received_at !== "string" ||
    typeof value.server_processed_at !== "string" ||
    typeof value.completion_effective_date !== "string" ||
    !positiveInteger(value.event_sequence) ||
    reversedAt === undefined ||
    deviceObservedAt === undefined ||
    deviceTimezoneName === undefined ||
    (value.client_time_valid !== null && typeof value.client_time_valid !== "boolean")
  ) return null;
  return {
    id: value.id,
    occurrenceId: value.occurrence_id,
    serverReceivedAt: value.server_received_at,
    serverProcessedAt: value.server_processed_at,
    completionEffectiveDate: value.completion_effective_date,
    eventSequence: value.event_sequence,
    reversedAt,
    deviceObservedAt,
    deviceTimezoneName,
    clientTimeValid: value.client_time_valid,
  };
}

function parseCampaign(value: unknown): CompletionCampaign | null {
  if (!isObject(value)) return null;
  const completedAt = nullableString(value.completed_at);
  if (
    typeof value.id !== "string" ||
    (value.status !== "active" && value.status !== "completed" && value.status !== "archived") ||
    !positiveInteger(value.record_version) ||
    completedAt === undefined
  ) return null;
  return {
    id: value.id,
    status: value.status,
    recordVersion: value.record_version,
    completedAt,
  };
}

function parseProgressEvent(value: unknown): ProgressEventReference | null {
  if (
    !isObject(value) ||
    typeof value.id !== "string" ||
    typeof value.event_type !== "string" ||
    !positiveInteger(value.event_sequence) ||
    typeof value.server_processed_at !== "string"
  ) return null;
  return {
    id: value.id,
    eventType: value.event_type,
    eventSequence: value.event_sequence,
    serverProcessedAt: value.server_processed_at,
  };
}

export function parseCompleteOccurrence(value: unknown): CompleteOccurrenceResult | null {
  if (
    !isObject(value) ||
    (value.outcome !== "completed" && value.outcome !== "duplicate_completion") ||
    !Array.isArray(value.progress_events)
  ) return null;
  const occurrence = parseOccurrence(value.occurrence);
  const completion = parseCompletion(value.completion);
  const campaign = parseCampaign(value.campaign);
  const progressEvents = value.progress_events.map(parseProgressEvent);
  if (!occurrence || !completion || !campaign || progressEvents.some((event) => !event)) return null;
  if (
    occurrence.id !== completion.occurrenceId ||
    occurrence.campaignId !== campaign.id
  ) return null;
  return {
    outcome: value.outcome,
    occurrence,
    completion,
    campaign,
    progressEvents: progressEvents as ProgressEventReference[],
  };
}

export function parseReverseCompletion(value: unknown): ReverseCompletionResult | null {
  if (
    !isObject(value) ||
    (value.outcome !== "reversed" && value.outcome !== "already_reversed") ||
    !Array.isArray(value.progress_events) ||
    !isObject(value.reversal)
  ) return null;
  const occurrence = parseOccurrence(value.occurrence);
  const completion = parseCompletion(value.completion);
  const campaign = parseCampaign(value.campaign);
  const progressEvents = value.progress_events.map(parseProgressEvent);
  const reversal = value.reversal;
  if (
    !occurrence || !completion || !campaign || progressEvents.some((event) => !event) ||
    typeof reversal.id !== "string" ||
    typeof reversal.completion_id !== "string" ||
    typeof reversal.occurrence_id !== "string" ||
    reversal.reason !== "user_correction" ||
    typeof reversal.server_received_at !== "string" ||
    typeof reversal.server_processed_at !== "string" ||
    !positiveInteger(reversal.event_sequence) ||
    reversal.completion_id !== completion.id ||
    reversal.occurrence_id !== occurrence.id ||
    completion.occurrenceId !== occurrence.id ||
    occurrence.campaignId !== campaign.id
  ) return null;
  return {
    outcome: value.outcome,
    occurrence,
    completion,
    reversal: {
      id: reversal.id,
      completionId: reversal.completion_id,
      occurrenceId: reversal.occurrence_id,
      reason: reversal.reason,
      serverReceivedAt: reversal.server_received_at,
      serverProcessedAt: reversal.server_processed_at,
      eventSequence: reversal.event_sequence,
    },
    campaign,
    progressEvents: progressEvents as ProgressEventReference[],
  };
}
