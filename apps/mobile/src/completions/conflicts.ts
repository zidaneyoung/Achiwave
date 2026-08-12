export interface CompletionConflictSnapshot {
  occurrence: {
    id: string;
    questId: string;
    campaignId: string;
    status: string;
    recordVersion: number;
  };
  campaign: {
    id: string;
    status: string;
    recordVersion: number;
  };
  activeCompletionId: string | null;
  eventSequence: number;
  progressEvents: Array<{
    id: string;
    eventType: string;
    eventSequence: number;
  }>;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function stringValue(source: Record<string, unknown>, key: string): string | null {
  const value = source[key];
  return typeof value === "string" && value.length > 0 ? value : null;
}

function positiveInteger(source: Record<string, unknown>, key: string): number | null {
  const value = source[key];
  return Number.isInteger(value) && (value as number) >= 1 ? value as number : null;
}

export function parseCompletionConflict(
  value: unknown,
): CompletionConflictSnapshot | null {
  if (!isObject(value) || !isObject(value.occurrence) || !isObject(value.campaign)) {
    return null;
  }
  const occurrenceId = stringValue(value.occurrence, "id");
  const questId = stringValue(value.occurrence, "quest_id");
  const campaignId = stringValue(value.occurrence, "campaign_id");
  const occurrenceStatus = stringValue(value.occurrence, "status");
  const occurrenceVersion = positiveInteger(value.occurrence, "record_version");
  const currentCampaignId = stringValue(value.campaign, "id");
  const campaignStatus = stringValue(value.campaign, "status");
  const campaignVersion = positiveInteger(value.campaign, "record_version");
  const eventSequence = typeof value.event_sequence === "number" &&
    Number.isInteger(value.event_sequence) && value.event_sequence >= 0
    ? value.event_sequence
    : null;
  const activeCompletionId = value.active_completion_id === null
    ? null
    : typeof value.active_completion_id === "string"
      ? value.active_completion_id
      : undefined;
  if (
    !occurrenceId || !questId || !campaignId || !occurrenceStatus ||
    !occurrenceVersion || !currentCampaignId || currentCampaignId !== campaignId ||
    !campaignStatus || !campaignVersion || eventSequence === null ||
    activeCompletionId === undefined || !Array.isArray(value.progress_events)
  ) return null;
  const progressEvents = value.progress_events.map((event) => {
    if (!isObject(event)) return null;
    const id = stringValue(event, "id");
    const eventType = stringValue(event, "event_type");
    const sequence = positiveInteger(event, "event_sequence");
    return id && eventType && sequence
      ? { id, eventType, eventSequence: sequence }
      : null;
  });
  if (progressEvents.some((event) => event === null)) return null;
  return {
    occurrence: {
      id: occurrenceId,
      questId,
      campaignId,
      status: occurrenceStatus,
      recordVersion: occurrenceVersion,
    },
    campaign: {
      id: currentCampaignId,
      status: campaignStatus,
      recordVersion: campaignVersion,
    },
    activeCompletionId,
    eventSequence,
    progressEvents: progressEvents as CompletionConflictSnapshot["progressEvents"],
  };
}
