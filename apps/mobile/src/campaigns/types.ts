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
