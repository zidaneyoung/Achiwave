import { ActivityIndicator, StyleSheet, View } from "react-native";

import { AppText } from "../theme/AppText";
import {
  type AchiwaveTheme,
  useAchiwaveTheme,
  useThemeStyles,
} from "../theme/ThemeProvider";
import { radii, spacing } from "../theme/tokens";
import { clampProgress } from "./progress";

export interface ProgressIndicatorProps {
  value?: number;
  label?: string;
  compact?: boolean;
  reduceMotion?: boolean;
}

export function ProgressIndicator({
  compact = false,
  label,
  reduceMotion = false,
  value,
}: ProgressIndicatorProps) {
  const theme = useAchiwaveTheme();
  const styles = useThemeStyles(createStyles);
  const determinate = value !== undefined;
  const progress = clampProgress(value ?? 0);
  const spokenLabel = label ?? (determinate ? `${Math.round(progress)}% complete` : "Loading");

  return (
    <View
      accessibilityLabel={spokenLabel}
      accessibilityRole="progressbar"
      accessibilityValue={determinate ? { min: 0, max: 100, now: progress } : { text: "In progress" }}
      style={styles.container}
    >
      {label ? (
        <View accessibilityElementsHidden style={styles.labelRow}>
          <AppText variant={compact ? "caption" : "label"}>{label}</AppText>
          {determinate ? <AppText tone="muted" variant="caption">{Math.round(progress)}%</AppText> : null}
        </View>
      ) : null}
      {determinate || reduceMotion ? (
        <View accessibilityElementsHidden style={[styles.track, compact && styles.compactTrack]}>
          <View
            style={[
              styles.fill,
              compact && styles.compactTrack,
              { width: `${determinate ? progress : 35}%` },
            ]}
          />
        </View>
      ) : (
        <ActivityIndicator
          accessibilityElementsHidden
          color={theme.colors.accent}
          size={compact ? "small" : "large"}
          style={styles.activity}
        />
      )}
    </View>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  container: { gap: spacing.xs },
  labelRow: { flexDirection: "row", justifyContent: "space-between" },
  track: {
    backgroundColor: theme.colors.surfaceElevated,
    borderRadius: radii.pill,
    height: spacing.xs,
    overflow: "hidden",
  },
  compactTrack: { height: spacing.xxs },
  fill: {
    backgroundColor: theme.colors.accent,
    borderRadius: radii.pill,
    height: spacing.xs,
  },
  activity: { alignSelf: "flex-start" },
});
