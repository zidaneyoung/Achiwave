import type { ReactNode } from "react";
import { Link, type Href } from "expo-router";
import { Pressable, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../theme/ThemeProvider";
import { AppText } from "../theme/AppText";
import { radii, sizing, spacing } from "../theme/tokens";

interface RootDestinationScreenProps {
  title: string;
  eyebrow: string;
  description: string;
  detailHref?: Href;
  detailLabel?: string;
  children?: ReactNode;
}

export function RootDestinationScreen({
  title,
  eyebrow,
  description,
  detailHref,
  detailLabel = "Open details",
  children,
}: RootDestinationScreenProps) {
  const styles = useThemeStyles(createStyles);
  return (
    <SafeAreaView edges={["top", "left", "right"]} style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <AppText tone="accent" variant="label" style={styles.eyebrow}>{eyebrow}</AppText>
        <AppText accessibilityRole="header" variant="display" style={styles.title}>
          {title}
        </AppText>
        <AppText tone="muted" style={styles.description}>{description}</AppText>
        {detailHref ? (
          <Link href={detailHref} asChild>
            <Pressable
              accessibilityRole="button"
              style={({ pressed }) => [
                styles.detailButton,
                pressed && styles.detailButtonPressed,
              ]}
            >
              <AppText tone="onAction" variant="label">{detailLabel}</AppText>
            </Pressable>
          </Link>
        ) : null}
        {children ? <View style={styles.actions}>{children}</View> : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: theme.colors.background },
  content: {
    flexGrow: 1,
    justifyContent: "center",
    padding: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  eyebrow: {
    letterSpacing: 1.2,
    textTransform: "uppercase",
  },
  title: {
    marginTop: spacing.xs,
  },
  description: {
    marginTop: spacing.sm,
    maxWidth: sizing.contentMeasure,
  },
  detailButton: {
    alignItems: "center",
    alignSelf: "flex-start",
    backgroundColor: theme.colors.action,
    borderRadius: radii.md,
    justifyContent: "center",
    marginTop: spacing.lg,
    minHeight: sizing.minimumTouchTarget,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  detailButtonPressed: { backgroundColor: theme.colors.actionPressed },
  actions: { marginTop: spacing.lg },
});
