export type QuestCategory = "personal" | "health" | "learning" | "work" | "finance";
export type QuestDifficulty = "easy" | "medium" | "hard";

export interface QuestAuthoringOption<TValue extends string = string> {
  value: TValue;
  label: string;
}

export interface QuestAuthoringOptions {
  categories: QuestAuthoringOption<QuestCategory>[];
  difficulties: QuestAuthoringOption<QuestDifficulty>[];
  rewardXpValues: number[];
}

export interface QuestOrderItem {
  id: string;
  displayOrder: number;
  recordVersion: number;
}

export interface QuestOrder {
  campaignId: string;
  campaignRecordVersion: number;
  items: QuestOrderItem[];
}

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
  category: QuestCategory | null;
  categoryLabel: string;
  difficulty: QuestDifficulty | null;
  difficultyLabel: string;
  rewardXp: number;
  displayOrder: number;
  availableFrom: string | null;
  dueAt: string | null;
  timezoneName: string | null;
  dueStatus: "none" | "upcoming" | "overdue" | "unavailable";
  recordVersion: number;
  archivedAt: string | null;
  restoredAt: string | null;
  createdAt: string;
  updatedAt: string;
  occurrence: OneTimeOccurrence | null;
}
