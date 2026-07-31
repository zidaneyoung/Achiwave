import { Link } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export default function LoginRoute() {
  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          Welcome back
        </Text>
        <Text style={styles.message}>
          Sign-in controls become available after protected credential storage is
          initialized.
        </Text>
        <Link href="/(auth)/register" asChild>
          <Pressable
            accessibilityHint="Opens account registration."
            accessibilityRole="button"
            style={({ pressed }) => [
              styles.button,
              pressed && styles.buttonPressed,
            ]}
          >
            <Text style={styles.buttonText}>Create an account</Text>
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
    backgroundColor: "#1d5b44",
    borderRadius: 10,
    justifyContent: "center",
    marginTop: 24,
    minHeight: 48,
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  buttonPressed: { backgroundColor: "#144432" },
  buttonText: { color: "#ffffff", fontSize: 17, fontWeight: "700" },
});
