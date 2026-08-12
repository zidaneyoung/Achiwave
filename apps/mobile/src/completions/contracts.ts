import type {
  CompleteOccurrenceResult,
  CompletionCampaign,
  CompletionOccurrence,
  CompletionRecord,
  ProgressEventReference,
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
  if (
    typeof value.id !== "string" ||
    typeof value.occurrence_id !== "string" ||
    typeof value.server_received_at !== "string" ||
    typeof value.server_processed_at !== "string" ||
    typeof value.completion_effective_date !== "string" ||
    !positiveInteger(value.event_sequence) ||
    reversedAt === undefined
  ) return null;
  return {
    id: value.id,
    occurrenceId: value.occurrence_id,
    serverReceivedAt: value.server_received_at,
    serverProcessedAt: value.server_processed_at,
    completionEffectiveDate: value.completion_effective_date,
    eventSequence: value.event_sequence,
    reversedAt,
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
