import type { TextStyle, ViewStyle } from "react-native";

export const spacing = {
  xxs: 4,
  xs: 8,
  sm: 12,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 40,
  xxxl: 48,
} as const;

export const radii = {
  sm: 8,
  md: 12,
  lg: 16,
  pill: 999,
} as const;

export const borders = {
  thin: 1,
  selected: 2,
} as const;

export const sizing = {
  minimumTouchTarget: 48,
  formControl: 52,
  badgeRegular: 28,
  badgeCompact: 24,
  skeletonAvatar: 64,
  skeletonBody: 72,
  compactViewportWidth: 320,
  compactViewportHeight: 568,
  contentMeasure: 520,
} as const;

export const elevation: Readonly<Record<"none" | "low", ViewStyle>> = {
  none: { elevation: 0, shadowOpacity: 0 },
  low: {
    elevation: 2,
    shadowColor: "#000000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.18,
    shadowRadius: 2,
  },
};

export type TypographyVariant =
  | "display"
  | "heading1"
  | "heading2"
  | "title"
  | "body"
  | "label"
  | "caption";

export const typography: Readonly<Record<TypographyVariant, TextStyle>> = {
  display: { fontSize: 32, fontWeight: "700", lineHeight: 38 },
  heading1: { fontSize: 28, fontWeight: "700", lineHeight: 34 },
  heading2: { fontSize: 22, fontWeight: "700", lineHeight: 28 },
  title: { fontSize: 18, fontWeight: "700", lineHeight: 24 },
  body: { fontSize: 16, fontWeight: "400", lineHeight: 24 },
  label: { fontSize: 14, fontWeight: "700", lineHeight: 20 },
  caption: { fontSize: 12, fontWeight: "400", lineHeight: 16 },
};
