import { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
} from "react-native";

import { useAuthentication } from "../../src/auth/AuthContext";
import { KeyboardAwareScreen } from "../../src/platform/KeyboardAwareScreen";
import {
  type AchiwaveTheme,
  useAchiwaveTheme,
  useThemeStyles,
} from "../../src/theme/ThemeProvider";

export default function AccountRoute() {
  const theme = useAchiwaveTheme();
  const styles = useThemeStyles(createStyles);
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
    <KeyboardAwareScreen contentContainerStyle={styles.container}>
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
              color={theme.colors.onAction}
            />
          ) : (
            <Text style={styles.dangerButtonText}>Deactivate account</Text>
          )}
        </Pressable>
    </KeyboardAwareScreen>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 24 },
  title: { color: theme.colors.foreground, fontSize: 30, fontWeight: "700" },
  message: { color: theme.colors.foregroundMuted, fontSize: 17, lineHeight: 24, marginTop: 12 },
  label: { color: theme.colors.foreground, fontSize: 17, fontWeight: "600", marginTop: 24 },
  input: {
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderRadius: 10,
    borderWidth: 1,
    color: theme.colors.foreground,
    fontSize: 17,
    marginTop: 8,
    minHeight: 52,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  error: { color: theme.colors.error, fontSize: 16, lineHeight: 22, marginTop: 16 },
  dangerButton: {
    alignItems: "center",
    backgroundColor: theme.colors.danger,
    borderRadius: 10,
    justifyContent: "center",
    marginTop: 24,
    minHeight: 52,
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  dangerButtonPressed: { backgroundColor: theme.colors.dangerPressed },
  dangerButtonText: { color: theme.colors.onAction, fontSize: 17, fontWeight: "700" },
  disabled: { opacity: 0.65 },
});
