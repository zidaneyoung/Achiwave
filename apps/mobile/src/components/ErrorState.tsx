import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import { StyleSheet, View } from "react-native";

import { AppButton } from "./AppButton";
import { AppText } from "../theme/AppText";
import { useAchiwaveTheme } from "../theme/ThemeProvider";
import { sizing, spacing } from "../theme/tokens";

export type ErrorStateKind =
  | "inline"
  | "section"
  | "fullScreen"
  | "validation"
  | "authentication"
  | "network";

const COPY: Record<ErrorStateKind, { title: string; description: string; retry: boolean }> = {
  inline: { title: "Could not update this item", description: "Your existing information is still available.", retry: false },
  section: { title: "This section is unavailable", description: "Other content on this screen is unchanged.", retry: true },
  fullScreen: { title: "Achiwave could not load", description: "Try again when you are ready.", retry: true },
  validation: { title: "Check the highlighted information", description: "Correct the field message and submit again.", retry: false },
  authentication: { title: "Sign-in could not be completed", description: "Check your details or connection and try again.", retry: true },
  network: { title: "Connection unavailable", description: "Reconnect before trying this action again.", retry: true },
};

export function ErrorState({ kind, onRetry }: { kind: ErrorStateKind; onRetry?: () => void }) {
  const theme = useAchiwaveTheme();
  const copy = COPY[kind];
  const compact = kind === "inline" || kind === "validation";
  return (
    <View
      accessibilityLiveRegion="assertive"
      accessibilityRole="alert"
      style={[styles.container, compact && styles.compact]}
    >
      <MaterialCommunityIcons
        accessibilityElementsHidden
        color={theme.colors.error}
        importantForAccessibility="no-hide-descendants"
        name="alert-circle-outline"
        size={compact ? sizing.iconMedium : sizing.iconLarge}
      />
      <View style={styles.copy}>
        <AppText tone="error" variant={compact ? "title" : "heading2"}>{copy.title}</AppText>
        <AppText tone="muted">{copy.description}</AppText>
      </View>
      {copy.retry && onRetry ? <AppButton label="Try again" onPress={onRetry} variant="secondary" /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: "flex-start", gap: spacing.sm, padding: spacing.lg },
  compact: { flexDirection: "row", padding: spacing.md },
  copy: { flex: 1, gap: spacing.xs },
});
