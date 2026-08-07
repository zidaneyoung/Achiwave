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

export function invalidateCachedCampaign(
  ownerId: string,
  campaignId: string,
): void {
  const lists = ownerCampaigns.get(ownerId);
  if (lists) {
    ownerCampaigns.set(ownerId, {
      active: lists.active?.filter((campaign) => campaign.id !== campaignId),
      archived: undefined,
    });
  }
  ownerCampaignDetails.get(ownerId)?.delete(campaignId);
}

export async function clearCachedCampaigns(): Promise<void> {
  ownerCampaigns.clear();
  ownerCampaignDetails.clear();
}
