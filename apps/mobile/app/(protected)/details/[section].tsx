import { Link, Stack, useLocalSearchParams } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import {
  DETAIL_COPY,
  isRootDestination,
  PROTECTED_ROUTES,
} from "../../../src/navigation/routes";

export default function ProtectedDetailRoute() {
  const { section } = useLocalSearchParams<{ section?: string | string[] }>();
  const copy = isRootDestination(section) ? DETAIL_COPY[section] : null;
  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.safeArea}>
      <Stack.Screen options={{ title: copy?.title ?? "Unavailable details" }} />
      <View style={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          {copy?.title ?? "This destination is unavailable"}
        </Text>
        <Text style={styles.description}>
          {copy?.description ?? "The requested protected route is not recognized."}
        </Text>
        {!copy ? (
          <Link href={PROTECTED_ROUTES.home} asChild>
            <Pressable
              accessibilityRole="button"
              style={({ pressed }) => [styles.button, pressed && styles.pressed]}
            >
              <Text style={styles.buttonText}>Return Home</Text>
            </Pressable>
          </Link>
        ) : null}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#171A21" },
  container: { flex: 1, justifyContent: "center", padding: 24 },
  title: { color: "#C7D5E0", fontSize: 28, fontWeight: "700", lineHeight: 34 },
  description: { color: "#A7B8C6", fontSize: 16, lineHeight: 24, marginTop: 12 },
  button: {
    alignItems: "center",
    alignSelf: "flex-start",
    backgroundColor: "#2A475E",
    borderRadius: 10,
    justifyContent: "center",
    marginTop: 24,
    minHeight: 48,
    paddingHorizontal: 18,
  },
  pressed: { backgroundColor: "#365E7A" },
  buttonText: { color: "#FFFFFF", fontSize: 16, fontWeight: "700" },
});
