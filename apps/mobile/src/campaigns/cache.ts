import type {
  CampaignDetail,
  CampaignListItem,
  CampaignListView,
} from "./types";

const ownerCampaigns = new Map<
  string,
  Partial<Record<CampaignListView, CampaignListItem[]>>
>();
const ownerCampaignDetails = new Map<
  string,
  Map<string, Partial<Record<"activeOnly" | "withArchived", CampaignDetail>>>
>();

export function getCachedCampaigns(
  ownerId: string,
  view: CampaignListView,
): CampaignListItem[] | null {
  return ownerCampaigns.get(ownerId)?.[view] ?? null;
}

export function setCachedCampaigns(
  ownerId: string,
  view: CampaignListView,
  items: CampaignListItem[],
): void {
  const existing = ownerCampaigns.get(ownerId) ?? {};
  ownerCampaigns.set(ownerId, { ...existing, [view]: items });
}

export function getCachedCampaignDetail(
  ownerId: string,
  campaignId: string,
  includeArchivedQuests: boolean,
): CampaignDetail | null {
  const key = includeArchivedQuests ? "withArchived" : "activeOnly";
  return ownerCampaignDetails.get(ownerId)?.get(campaignId)?.[key] ?? null;
}

export function setCachedCampaignDetail(
  ownerId: string,
  campaignId: string,
  includeArchivedQuests: boolean,
  detail: CampaignDetail,
): void {
  const ownerDetails = ownerCampaignDetails.get(ownerId) ?? new Map();
  const existing = ownerDetails.get(campaignId) ?? {};
  const key = includeArchivedQuests ? "withArchived" : "activeOnly";
  ownerDetails.set(campaignId, { ...existing, [key]: detail });
  ownerCampaignDetails.set(ownerId, ownerDetails);
}

export async function clearCachedCampaigns(): Promise<void> {
  ownerCampaigns.clear();
  ownerCampaignDetails.clear();
}
