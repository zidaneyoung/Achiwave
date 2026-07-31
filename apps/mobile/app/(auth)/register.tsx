import { Link } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export default function RegistrationRoute() {
  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          Create your account
        </Text>
        <Text style={styles.message}>
          Account registration will store credentials only in the protected
          platform container.
        </Text>
        <Link href="/(auth)/login" asChild>
          <Pressable
            accessibilityHint="Returns to sign in."
            accessibilityRole="button"
            style={({ pressed }) => [
              styles.button,
              pressed && styles.buttonPressed,
            ]}
          >
            <Text style={styles.buttonText}>Back to sign in</Text>
          </Pressable>
        </Link>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#f7f5ef" },
  container: { flex: 1, justifyContent: "center", padding: 24 },
  title: { color: "#17221d", fontSize: 32, fontWeight: "700" },
  message: { color: "#35423b", fontSize: 17, lineHeight: 24, marginTop: 12 },
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
