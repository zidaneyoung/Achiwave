import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import { StyleSheet, View } from "react-native";

import { AppButton } from "./AppButton";
import { AppText } from "../theme/AppText";
import { useAchiwaveTheme } from "../theme/ThemeProvider";
import { sizing, spacing } from "../theme/tokens";

export type EmptyStateKind = "firstUse" | "filtered" | "completed" | "unavailable";

const ICONS = {
  firstUse: "compass-outline",
  filtered: "filter-off-outline",
  completed: "check-circle-outline",
  unavailable: "cloud-off-outline",
} as const;

export function EmptyState({
  actionLabel,
  description,
  kind,
  onAction,
  title,
}: {
  actionLabel?: string;
  description: string;
  kind: EmptyStateKind;
  onAction?: () => void;
  title: string;
}) {
  const theme = useAchiwaveTheme();
  return (
    <View style={styles.container}>
      <MaterialCommunityIcons
        accessibilityElementsHidden
        color={theme.colors.accent}
        importantForAccessibility="no-hide-descendants"
        name={ICONS[kind]}
        size={sizing.iconLarge}
      />
      <AppText accessibilityRole="header" variant="heading2" style={styles.center}>{title}</AppText>
      <AppText tone="muted" style={styles.center}>{description}</AppText>
      {actionLabel && onAction ? <AppButton label={actionLabel} onPress={onAction} variant="secondary" /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: "center", gap: spacing.sm, padding: spacing.lg },
  center: { textAlign: "center" },
});
