import type { ViewStyle } from "react-native";

import { sizing, spacing } from "../theme/tokens";

export const minimumTouchTargetStyle: ViewStyle = {
  minHeight: sizing.minimumTouchTarget,
  minWidth: sizing.minimumTouchTarget,
};

export const compactControlHitSlop = {
  bottom: spacing.xs,
  left: spacing.xs,
  right: spacing.xs,
  top: spacing.xs,
} as const;
