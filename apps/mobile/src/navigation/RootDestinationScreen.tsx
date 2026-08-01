import type { ReactNode } from "react";
import { Link, type Href } from "expo-router";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

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
  detailButton: {
    alignItems: "center",
    alignSelf: "flex-start",
    backgroundColor: "#2A475E",
    borderRadius: 10,
    justifyContent: "center",
    marginTop: 24,
    minHeight: 48,
    paddingHorizontal: 18,
    paddingVertical: 12,
  },
  detailButtonPressed: { backgroundColor: "#365E7A" },
  detailButtonText: { color: "#FFFFFF", fontSize: 16, fontWeight: "700" },
  actions: { marginTop: 24 },
});
