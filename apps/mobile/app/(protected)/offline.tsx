import { Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuthentication } from "../../src/auth/AuthContext";

export default function OfflineLimitedRoute() {
  const { revalidate } = useAuthentication();

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          You are offline
        </Text>
        <Text style={styles.message}>
          A previously confirmed session is present, but no private feature data is
          available for offline use yet. Reconnect before making changes.
        </Text>
        <Pressable
          accessibilityHint="Checks the saved session with the Achiwave service."
          accessibilityRole="button"
          onPress={() => void revalidate()}
          style={({ pressed }) => [
            styles.button,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.buttonText}>Check connection</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#f7f5ef" },
  container: { flex: 1, justifyContent: "center", padding: 24 },
  title: { color: "#17221d", fontSize: 30, fontWeight: "700", textAlign: "center" },
  message: {
    color: "#35423b",
    fontSize: 17,
    lineHeight: 24,
    marginTop: 12,
    textAlign: "center",
  },
  button: {
    alignItems: "center",
    backgroundColor: "#1d5b44",
    borderRadius: 10,
    justifyContent: "center",
    marginTop: 24,
    minHeight: 52,
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  buttonPressed: { backgroundColor: "#144432" },
  buttonText: { color: "#ffffff", fontSize: 17, fontWeight: "700" },
});
