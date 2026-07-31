import { Link } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuthentication } from "../../src/auth/AuthContext";

export default function ProtectedHomeRoute() {
  const { state, signOut } = useAuthentication();
  if (state.status !== "authenticated") {
    return null;
  }
  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          Signed in
        </Text>
        <Text style={styles.message}>{state.user.email}</Text>
        <Link href="/(protected)/security" asChild>
          <Pressable
            accessibilityHint="Shows devices and sessions that can access this account."
            accessibilityRole="button"
            style={({ pressed }) => [
              styles.button,
              pressed && styles.buttonPressed,
            ]}
          >
            <Text style={styles.buttonText}>Devices and sessions</Text>
          </Pressable>
        </Link>
        <Link href="/(protected)/preferences" asChild>
          <Pressable
            accessibilityHint="Opens your presentation preferences."
            accessibilityRole="button"
            style={({ pressed }) => [
              styles.button,
              pressed && styles.buttonPressed,
            ]}
          >
            <Text style={styles.buttonText}>Preferences</Text>
          </Pressable>
        </Link>
        <Pressable
          accessibilityHint="Ends this session and removes local credentials."
          accessibilityRole="button"
          onPress={() => void signOut()}
          style={({ pressed }) => [
            styles.button,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.buttonText}>Sign out</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#f7f5ef" },
  container: { flex: 1, justifyContent: "center", padding: 24 },
  title: { color: "#17221d", fontSize: 32, fontWeight: "700" },
  message: { color: "#35423b", fontSize: 17, marginTop: 12 },
  button: {
    alignItems: "center",
    borderColor: "#1d5b44",
    borderRadius: 10,
    borderWidth: 2,
    justifyContent: "center",
    marginTop: 24,
    minHeight: 48,
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  buttonPressed: { backgroundColor: "#e1ebe5" },
  buttonText: { color: "#1d5b44", fontSize: 17, fontWeight: "700" },
});
