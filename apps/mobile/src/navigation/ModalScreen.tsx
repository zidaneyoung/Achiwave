import type { ReactNode } from "react";
import { router } from "expo-router";
import { Pressable, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../theme/ThemeProvider";
import { AppText } from "../theme/AppText";
import { radii, sizing, spacing } from "../theme/tokens";
import { PROTECTED_ROUTES } from "./routes";

interface ModalScreenProps {
  title: string;
  description: string;
  children?: ReactNode;
}

export function ModalScreen({ title, description, children }: ModalScreenProps) {
  const styles = useThemeStyles(createStyles);
  function dismiss(): void {
    if (router.canGoBack()) {
      router.back();
      return;
    }
    router.replace(PROTECTED_ROUTES.home);
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View
        accessibilityViewIsModal
        importantForAccessibility="yes"
        style={styles.surface}
      >
        <ScrollView contentContainerStyle={styles.content}>
          <AppText accessibilityRole="header" variant="heading1">
            {title}
          </AppText>
          <AppText tone="muted" style={styles.description}>{description}</AppText>
          {children}
        </ScrollView>
        <Pressable
          accessibilityHint="Dismisses this temporary screen and returns to the previous context."
          accessibilityLabel="Close modal"
          accessibilityRole="button"
          onPress={dismiss}
          style={({ pressed }) => [styles.closeButton, pressed && styles.pressed]}
        >
          <AppText tone="onAction" variant="label">Close</AppText>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: theme.colors.background },
  surface: { flex: 1, backgroundColor: theme.colors.surface },
  content: { flexGrow: 1, justifyContent: "center", padding: spacing.lg },
  description: { marginTop: spacing.sm },
  closeButton: {
    alignItems: "center",
    alignSelf: "stretch",
    backgroundColor: theme.colors.action,
    borderRadius: radii.md,
    justifyContent: "center",
    margin: spacing.lg,
    minHeight: sizing.minimumTouchTarget,
    paddingHorizontal: spacing.md,
  },
  pressed: { backgroundColor: theme.colors.actionPressed },
});
