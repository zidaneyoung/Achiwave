import { StyleSheet, View } from "react-native";

import { AppText } from "../theme/AppText";
import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../theme/ThemeProvider";
import { borders, radii, spacing } from "../theme/tokens";

export type SynchronizationState =
  | { status: "offline" }
  | { status: "reconnecting" }
  | { status: "pending"; pendingCount?: number }
  | { status: "synchronizing" }
  | { status: "synchronized"; confirmedAt: string }
  | { status: "failed" };

const COPY = {
  offline: ["Offline", "Read-only content may be limited until you reconnect."],
  reconnecting: ["Reconnecting", "Checking for a connection."],
  pending: ["Pending synchronization", "Changes have not been confirmed by the service."],
  synchronizing: ["Synchronizing", "Waiting for service confirmation."],
  synchronized: ["Synchronized", "The service confirmed the latest synchronization."],
  failed: ["Synchronization failed", "Some changes remain unconfirmed."],
} as const;

export function SyncIndicator({ state }: { state: SynchronizationState }) {
  const styles = useThemeStyles(createStyles);
  const [title, baseDescription] = COPY[state.status];
  const description =
    state.status === "pending" && state.pendingCount
      ? `${state.pendingCount} ${state.pendingCount === 1 ? "change is" : "changes are"} still pending.`
      : baseDescription;
  return (
    <View
      accessible
      accessibilityLiveRegion={state.status === "synchronized" ? "polite" : "assertive"}
      accessibilityRole="alert"
      style={[styles.base, styles[state.status]]}
    >
      <AppText variant="label">{title}</AppText>
      <AppText tone="muted" variant="caption">{description}</AppText>
    </View>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  base: {
    borderRadius: radii.md,
    borderWidth: borders.thin,
    gap: spacing.xxs,
    padding: spacing.sm,
  },
  offline: { backgroundColor: theme.colors.warningSurface, borderColor: theme.colors.warning },
  reconnecting: { backgroundColor: theme.colors.infoSurface, borderColor: theme.colors.info },
  pending: { backgroundColor: theme.colors.warningSurface, borderColor: theme.colors.warning },
  synchronizing: { backgroundColor: theme.colors.infoSurface, borderColor: theme.colors.info },
  synchronized: { backgroundColor: theme.colors.successSurface, borderColor: theme.colors.success },
  failed: { backgroundColor: theme.colors.errorSurface, borderColor: theme.colors.error },
});
