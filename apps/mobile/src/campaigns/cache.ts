import type { CampaignListItem, CampaignListView } from "./types";

const ownerCampaigns = new Map<
  string,
  Partial<Record<CampaignListView, CampaignListItem[]>>
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

export async function clearCachedCampaigns(): Promise<void> {
  ownerCampaigns.clear();
}
