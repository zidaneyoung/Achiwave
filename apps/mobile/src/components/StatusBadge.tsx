import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import { StyleSheet, View } from "react-native";

import { AppText } from "../theme/AppText";
import { useAchiwaveTheme, useThemeStyles } from "../theme/ThemeProvider";
import { borders, radii, sizing, spacing } from "../theme/tokens";

export type StatusTone = "neutral" | "success" | "warning" | "error" | "info";

export interface StatusBadgeProps {
  label: string;
  tone?: StatusTone;
  compact?: boolean;
}

const ICONS = {
  neutral: "circle-outline",
  success: "check-circle-outline",
  warning: "alert-outline",
  error: "alert-circle-outline",
  info: "information-outline",
} as const;

export function StatusBadge({
  compact = false,
  label,
  tone = "neutral",
}: StatusBadgeProps) {
  const theme = useAchiwaveTheme();
  const styles = useThemeStyles(createStyles);
  const colors = {
    neutral: theme.colors.foregroundMuted,
    success: theme.colors.success,
    warning: theme.colors.warning,
    error: theme.colors.error,
    info: theme.colors.info,
  };
  return (
    <View
      accessible
      accessibilityLabel={label}
      accessibilityRole="text"
      style={[
        styles.base,
        compact && styles.compact,
        { borderColor: colors[tone] },
      ]}
    >
      <MaterialCommunityIcons
        accessibilityElementsHidden
        color={colors[tone]}
        importantForAccessibility="no-hide-descendants"
        name={ICONS[tone]}
        size={compact ? 14 : 16}
      />
      <AppText
        style={{ color: colors[tone] }}
        variant="caption"
      >
        {label}
      </AppText>
    </View>
  );
}

const createStyles = () => StyleSheet.create({
  base: {
    alignItems: "center",
    alignSelf: "flex-start",
    borderRadius: radii.pill,
    borderWidth: borders.thin,
    flexDirection: "row",
    gap: spacing.xs,
    minHeight: sizing.badgeRegular,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xxs,
  },
  compact: { gap: spacing.xxs, minHeight: sizing.badgeCompact, paddingHorizontal: spacing.xs },
});
