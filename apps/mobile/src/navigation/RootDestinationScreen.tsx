import type { ReactNode } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

interface RootDestinationScreenProps {
  title: string;
  eyebrow: string;
  description: string;
  children?: ReactNode;
}

export function RootDestinationScreen({
  title,
  eyebrow,
  description,
  children,
}: RootDestinationScreenProps) {
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
        {children ? <View style={styles.actions}>{children}</View> : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#171A21" },
  content: {
    flexGrow: 1,
    justifyContent: "center",
    padding: 24,
    paddingBottom: 40,
  },
  eyebrow: {
    color: "#66C0F4",
    fontSize: 14,
    fontWeight: "700",
    letterSpacing: 1.2,
    textTransform: "uppercase",
  },
  title: {
    color: "#C7D5E0",
    fontSize: 32,
    fontWeight: "700",
    lineHeight: 38,
    marginTop: 8,
  },
  description: {
    color: "#A7B8C6",
    fontSize: 16,
    lineHeight: 24,
    marginTop: 12,
    maxWidth: 520,
  },
  actions: { marginTop: 24 },
});
