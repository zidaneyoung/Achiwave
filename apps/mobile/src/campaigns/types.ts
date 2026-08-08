export type CampaignStatus = "active" | "completed" | "archived";

export interface Campaign {
  id: string;
  title: string;
  description: string | null;
  displayOrder: number;
  status: CampaignStatus;
  recordVersion: number;
  completedAt: string | null;
  archivedAt: string | null;
  restoredAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CampaignQuestSummary {
  active: number;
  archived: number;
  total: number;
}

export interface CampaignListItem extends Campaign {
  questSummary: CampaignQuestSummary;
}

export interface CampaignListPage {
  items: CampaignListItem[];
  total: number;
  limit: number;
  offset: number;
}

export type CampaignListView = "active" | "archived";

export type QuestDisplayStatus =
  | "active"
  | "archived"
  | "scheduled"
  | "available"
  | "completed"
  | "reversed"
  | "expired"
  | "voided";

export interface CampaignQuest {
  id: string;
  campaignId: string;
  questType: "one_time" | "recurring";
  definitionState: "active" | "archived";
  status: QuestDisplayStatus;
  title: string;
  description: string | null;
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
}

export interface CampaignDetail extends Campaign {
  questSummary: CampaignQuestSummary;
  quests: CampaignQuest[];
}
