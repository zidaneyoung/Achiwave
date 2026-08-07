import type { Href } from "expo-router";

import type { RootDestinationName } from "./rootDestinations";

export const PROTECTED_ROUTES = {
  home: "/(protected)/(tabs)/home" as const satisfies Href,
  campaigns: "/(protected)/(tabs)/campaigns" as const satisfies Href,
  campaignCreate: "/(protected)/campaigns/new" as const satisfies Href,
  campaignDetail(campaignId: string) {
    return {
      pathname: "/(protected)/campaigns/[campaignId]",
      params: { campaignId },
    } as const satisfies Href;
  },
  campaignEdit(campaignId: string) {
    return {
      pathname: "/(protected)/campaigns/[campaignId]/edit",
      params: { campaignId },
    } as const satisfies Href;
  },
  questCreate(campaignId: string) {
    return {
      pathname: "/(protected)/campaigns/[campaignId]/quests/new",
      params: { campaignId },
    } as const satisfies Href;
  },
  progress: "/(protected)/(tabs)/progress" as const satisfies Href,
  profile: "/(protected)/(tabs)/profile" as const satisfies Href,
  security: "/(protected)/security" as const satisfies Href,
  preferences: "/(protected)/preferences" as const satisfies Href,
  account: "/(protected)/account" as const satisfies Href,
  designSystem: "/(protected)/design-system" as const satisfies Href,
  modal: "/(protected)/modal" as const satisfies Href,
  detail(section: RootDestinationName) {
    return {
      pathname: "/(protected)/details/[section]",
      params: { section },
    } as const satisfies Href;
  },
};

export function isRootDestination(
  value: string | string[] | undefined,
): value is RootDestinationName {
  return (
    value === "home" ||
    value === "campaigns" ||
    value === "progress" ||
    value === "profile"
  );
}

export const DETAIL_COPY: Readonly<
  Record<RootDestinationName, { title: string; description: string }>
> = {
  home: {
    title: "Home details",
    description: "This typed route proves stack drill-down and native back behavior without adding later-stage product data.",
  },
  campaigns: {
    title: "Campaigns details",
    description: "Campaign creation and campaign lists remain deferred to Stage 6.",
  },
  progress: {
    title: "Progress details",
    description: "Only backend-confirmed progression will be presented when its roadmap stage is implemented.",
  },
  profile: {
    title: "Profile details",
    description: "Account and preference tools remain protected by the Stage 4 session boundary.",
  },
};
