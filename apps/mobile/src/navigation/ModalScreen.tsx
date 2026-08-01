import type { ReactNode } from "react";
import { router } from "expo-router";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { PROTECTED_ROUTES } from "./routes";

interface ModalScreenProps {
  title: string;
  description: string;
  children?: ReactNode;
}

export function ModalScreen({ title, description, children }: ModalScreenProps) {
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

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#111820" },
  surface: { flex: 1, backgroundColor: "#1B2838" },
  content: { flexGrow: 1, justifyContent: "center", padding: 24 },
  title: { color: "#C7D5E0", fontSize: 28, fontWeight: "700", lineHeight: 34 },
  description: { color: "#A7B8C6", fontSize: 16, lineHeight: 24, marginTop: 12 },
  closeButton: {
    alignItems: "center",
    alignSelf: "stretch",
    backgroundColor: "#2A475E",
    borderRadius: 10,
    justifyContent: "center",
    margin: 24,
    minHeight: 48,
    paddingHorizontal: 18,
  },
  pressed: { backgroundColor: "#365E7A" },
  closeButtonText: { color: "#FFFFFF", fontSize: 16, fontWeight: "700" },
});
