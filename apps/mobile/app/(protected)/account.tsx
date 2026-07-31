import { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuthentication } from "../../src/auth/AuthContext";

export default function AccountRoute() {
  const { deactivateAccount } = useAuthentication();
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function deactivate(): Promise<void> {
    if (!password || submitting) {
      setMessage("Enter your password to confirm deactivation.");
      return;
    }
    setSubmitting(true);
    setMessage(null);
    try {
      await deactivateAccount(password);
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Account deactivation could not be completed.",
      );
    } finally {
      setSubmitting(false);
      setPassword("");
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          Account
        </Text>
        <Text style={styles.message}>
          Deactivation signs out every device and stops future access. It does not
          permanently delete your retained history.
        </Text>
        <Text style={styles.label}>Confirm password</Text>
        <TextInput
          accessibilityLabel="Confirm password"
          autoCapitalize="none"
          autoComplete="current-password"
          editable={!submitting}
          onChangeText={setPassword}
          secureTextEntry
          style={styles.input}
          textContentType="password"
          value={password}
        />
        {message ? (
          <Text
            accessibilityLiveRegion="assertive"
            accessibilityRole="alert"
            style={styles.error}
          >
            {message}
          </Text>
        ) : null}
        <Pressable
          accessibilityHint="Deactivates this account and signs out all devices."
          accessibilityRole="button"
          disabled={submitting}
          onPress={() => void deactivate()}
          style={({ pressed }) => [
            styles.dangerButton,
            pressed && styles.dangerButtonPressed,
            submitting && styles.disabled,
          ]}
        >
          {submitting ? (
            <ActivityIndicator
              accessibilityLabel="Deactivating account"
              color="#ffffff"
            />
          ) : (
            <Text style={styles.dangerButtonText}>Deactivate account</Text>
          )}
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#f7f5ef" },
  container: { flex: 1, justifyContent: "center", padding: 24 },
  title: { color: "#17221d", fontSize: 30, fontWeight: "700" },
  message: { color: "#35423b", fontSize: 17, lineHeight: 24, marginTop: 12 },
  label: { color: "#17221d", fontSize: 17, fontWeight: "600", marginTop: 24 },
  input: {
    backgroundColor: "#ffffff",
    borderColor: "#66746c",
    borderRadius: 10,
    borderWidth: 1,
    color: "#17221d",
    fontSize: 17,
    marginTop: 8,
    minHeight: 52,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  error: { color: "#9f241d", fontSize: 16, lineHeight: 22, marginTop: 16 },
  dangerButton: {
    alignItems: "center",
    backgroundColor: "#9f241d",
    borderRadius: 10,
    justifyContent: "center",
    marginTop: 24,
    minHeight: 52,
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  dangerButtonPressed: { backgroundColor: "#761a16" },
  dangerButtonText: { color: "#ffffff", fontSize: 17, fontWeight: "700" },
  disabled: { opacity: 0.65 },
});
