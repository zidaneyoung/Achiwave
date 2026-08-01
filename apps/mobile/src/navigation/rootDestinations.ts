import type { ComponentProps } from "react";
import type MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";

export type RootDestinationName = "home" | "campaigns" | "progress" | "profile";
type MaterialIconName = ComponentProps<typeof MaterialCommunityIcons>["name"];

export interface RootDestination {
  name: RootDestinationName;
  label: string;
  accessibilityLabel: string;
  icon: MaterialIconName;
  selectedIcon: MaterialIconName;
}

export const ROOT_DESTINATIONS: readonly RootDestination[] = [
  {
    name: "home",
    label: "Home",
    accessibilityLabel: "Home tab",
    icon: "home-variant-outline",
    selectedIcon: "home-variant",
  },
  {
    name: "campaigns",
    label: "Campaigns",
    accessibilityLabel: "Campaigns tab",
    icon: "flag-variant-outline",
    selectedIcon: "flag-variant",
  },
  {
    name: "progress",
    label: "Progress",
    accessibilityLabel: "Progress tab",
    icon: "chart-line-variant",
    selectedIcon: "chart-line",
  },
  {
    name: "profile",
    label: "Profile",
    accessibilityLabel: "Profile tab",
    icon: "account-circle-outline",
    selectedIcon: "account-circle",
  },
] as const;
