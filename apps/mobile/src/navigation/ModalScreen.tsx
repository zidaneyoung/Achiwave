import type { ReactNode } from "react";
import { router } from "expo-router";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../theme/ThemeProvider";
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
          <Text accessibilityRole="header" style={styles.title}>
            {title}
          </Text>
          <Text style={styles.description}>{description}</Text>
          {children}
        </ScrollView>
        <Pressable
          accessibilityHint="Dismisses this temporary screen and returns to the previous context."
          accessibilityLabel="Close modal"
          accessibilityRole="button"
          onPress={dismiss}
          style={({ pressed }) => [styles.closeButton, pressed && styles.pressed]}
        >
          <Text style={styles.closeButtonText}>Close</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: theme.colors.background },
  surface: { flex: 1, backgroundColor: theme.colors.surface },
  content: { flexGrow: 1, justifyContent: "center", padding: 24 },
  title: { color: theme.colors.foreground, fontSize: 28, fontWeight: "700", lineHeight: 34 },
  description: { color: theme.colors.foregroundMuted, fontSize: 16, lineHeight: 24, marginTop: 12 },
  closeButton: {
    alignItems: "center",
    alignSelf: "stretch",
    backgroundColor: theme.colors.action,
    borderRadius: 10,
    justifyContent: "center",
    margin: 24,
    minHeight: 48,
    paddingHorizontal: 18,
  },
  pressed: { backgroundColor: theme.colors.actionPressed },
  closeButtonText: { color: theme.colors.onAction, fontSize: 16, fontWeight: "700" },
});
