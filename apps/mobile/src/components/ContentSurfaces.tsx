import type { ReactNode } from "react";
import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import { Pressable, StyleSheet, View } from "react-native";

import { AppText } from "../theme/AppText";
import {
  type AchiwaveTheme,
  useAchiwaveTheme,
  useThemeStyles,
} from "../theme/ThemeProvider";
import { borders, radii, sizing, spacing } from "../theme/tokens";

interface SurfaceCopy {
  title: string;
  metadata?: string;
  status?: string;
  leading?: ReactNode;
}

export interface AppCardProps extends SurfaceCopy {
  children?: ReactNode;
  onPress?: () => void;
  accessibilityHint?: string;
}

export function AppCard({
  accessibilityHint,
  children,
  leading,
  metadata,
  onPress,
  status,
  title,
}: AppCardProps) {
  const theme = useAchiwaveTheme();
  const styles = useThemeStyles(createStyles);
  const content = (
    <View style={styles.cardContent}>
      {leading ? <View style={styles.leading}>{leading}</View> : null}
      <View style={styles.copy}>
        <AppText variant="title">{title}</AppText>
        {metadata ? <AppText tone="muted" variant="caption" style={styles.metadata}>{metadata}</AppText> : null}
        {status ? <AppText tone="info" variant="label" style={styles.metadata}>{status}</AppText> : null}
        {children ? <View style={styles.body}>{children}</View> : null}
      </View>
    </View>
  );
  if (!onPress) {
    return <View style={[styles.surface, styles.card]}>{content}</View>;
  }
  return (
    <Pressable
      accessibilityHint={accessibilityHint}
      accessibilityLabel={[title, metadata, status].filter(Boolean).join(", ")}
      accessibilityRole="button"
      android_ripple={{ color: theme.colors.surfacePressed }}
      onPress={onPress}
      style={({ pressed }) => [styles.surface, styles.card, pressed && styles.pressed]}
    >
      {content}
    </Pressable>
  );
}

export interface AppListItemProps extends SurfaceCopy {
  onPress?: () => void;
  trailingActionLabel?: string;
  onTrailingActionPress?: () => void;
}

export function AppListItem({
  leading,
  metadata,
  onPress,
  onTrailingActionPress,
  status,
  title,
  trailingActionLabel,
}: AppListItemProps) {
  const theme = useAchiwaveTheme();
  const styles = useThemeStyles(createStyles);
  const content = (
    <>
      {leading ? <View style={styles.leading}>{leading}</View> : null}
      <View style={styles.copy}>
        <AppText variant="title">{title}</AppText>
        {metadata ? <AppText tone="muted" variant="caption">{metadata}</AppText> : null}
        {status ? <AppText tone="info" variant="label">{status}</AppText> : null}
      </View>
      {trailingActionLabel && onTrailingActionPress ? (
        <Pressable
          accessibilityLabel={trailingActionLabel}
          accessibilityRole="button"
          hitSlop={spacing.xs}
          onPress={(event) => {
            event.stopPropagation();
            onTrailingActionPress();
          }}
          style={({ pressed }) => [styles.trailingAction, pressed && styles.pressed]}
        >
          <MaterialCommunityIcons
            accessibilityElementsHidden
            color={theme.colors.foreground}
            importantForAccessibility="no-hide-descendants"
            name="dots-vertical"
            size={24}
          />
        </Pressable>
      ) : null}
    </>
  );
  if (!onPress) {
    return <View style={[styles.surface, styles.listItem]}>{content}</View>;
  }
  return (
    <Pressable
      accessibilityLabel={[title, metadata, status].filter(Boolean).join(", ")}
      accessibilityRole="button"
      android_ripple={{ color: theme.colors.surfacePressed }}
      onPress={onPress}
      style={({ pressed }) => [styles.surface, styles.listItem, pressed && styles.pressed]}
    >
      {content}
    </Pressable>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  surface: {
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderRadius: radii.md,
    borderWidth: borders.thin,
  },
  card: { padding: spacing.md },
  cardContent: { flexDirection: "row" },
  listItem: {
    alignItems: "center",
    flexDirection: "row",
    minHeight: sizing.minimumTouchTarget,
    padding: spacing.md,
  },
  copy: { flex: 1, gap: spacing.xxs },
  leading: { marginRight: spacing.sm },
  metadata: { marginTop: spacing.xxs },
  body: { marginTop: spacing.sm },
  pressed: { backgroundColor: theme.colors.surfacePressed },
  trailingAction: {
    alignItems: "center",
    justifyContent: "center",
    marginLeft: spacing.xs,
    minHeight: sizing.minimumTouchTarget,
    minWidth: sizing.minimumTouchTarget,
  },
});
