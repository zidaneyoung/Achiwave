import type { ReactNode } from "react";
import { Link, type Href } from "expo-router";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../theme/ThemeProvider";

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
        <Text style={styles.eyebrow}>{eyebrow}</Text>
        <Text accessibilityRole="header" style={styles.title}>
          {title}
        </Text>
        <Text style={styles.description}>{description}</Text>
        {detailHref ? (
          <Link href={detailHref} asChild>
            <Pressable
              accessibilityRole="button"
              style={({ pressed }) => [
                styles.detailButton,
                pressed && styles.detailButtonPressed,
              ]}
            >
              <Text style={styles.detailButtonText}>{detailLabel}</Text>
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
    padding: 24,
    paddingBottom: 40,
  },
  eyebrow: {
    color: theme.colors.accent,
    fontSize: 14,
    fontWeight: "700",
    letterSpacing: 1.2,
    textTransform: "uppercase",
  },
  title: {
    color: theme.colors.foreground,
    fontSize: 32,
    fontWeight: "700",
    lineHeight: 38,
    marginTop: 8,
  },
  description: {
    color: theme.colors.foregroundMuted,
    fontSize: 16,
    lineHeight: 24,
    marginTop: 12,
    maxWidth: 520,
  },
  detailButton: {
    alignItems: "center",
    alignSelf: "flex-start",
    backgroundColor: theme.colors.action,
    borderRadius: 10,
    justifyContent: "center",
    marginTop: 24,
    minHeight: 48,
    paddingHorizontal: 18,
    paddingVertical: 12,
  },
  detailButtonPressed: { backgroundColor: theme.colors.actionPressed },
  detailButtonText: { color: theme.colors.onAction, fontSize: 16, fontWeight: "700" },
  actions: { marginTop: 24 },
});
