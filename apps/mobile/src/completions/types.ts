export interface CompletionOccurrence {
  id: string;
  questId: string;
  campaignId: string;
  status: "scheduled" | "available" | "completed" | "reversed" | "expired" | "voided";
  recordVersion: number;
  completedAt: string | null;
  reversedAt: string | null;
}

export interface CompletionRecord {
  id: string;
  occurrenceId: string;
  serverReceivedAt: string;
  serverProcessedAt: string;
  completionEffectiveDate: string;
  eventSequence: number;
  reversedAt: string | null;
}

export interface CompletionCampaign {
  id: string;
  status: "active" | "completed" | "archived";
  recordVersion: number;
  completedAt: string | null;
}

export interface ProgressEventReference {
  id: string;
  eventType: string;
  eventSequence: number;
  serverProcessedAt: string;
}

export interface CompleteOccurrenceResult {
  outcome: "completed" | "duplicate_completion";
  occurrence: CompletionOccurrence;
  completion: CompletionRecord;
  campaign: CompletionCampaign;
  progressEvents: ProgressEventReference[];
}
