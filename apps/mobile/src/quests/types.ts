export interface OneTimeOccurrence {
  id: string;
  status: "scheduled" | "available" | "completed" | "reversed" | "expired" | "voided";
  occurrenceLocalDate: string;
  timezoneName: string;
  availableAt: string;
  eligibilityExpiresAt: string | null;
  rewardXp: number;
  recordVersion: number;
}

export interface Quest {
  id: string;
  campaignId: string;
  campaignRecordVersion: number;
  campaignStatus: "active" | "completed" | "archived";
  questType: "one_time" | "recurring";
  definitionState: "active" | "archived";
  title: string;
  description: string | null;
  rewardXp: number;
  displayOrder: number;
  availableFrom: string | null;
  dueAt: string | null;
  timezoneName: string | null;
  recordVersion: number;
  archivedAt: string | null;
  restoredAt: string | null;
  createdAt: string;
  updatedAt: string;
  occurrence: OneTimeOccurrence | null;
}
