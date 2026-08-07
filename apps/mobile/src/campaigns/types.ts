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
