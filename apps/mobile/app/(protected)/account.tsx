import { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  TextInput,
} from "react-native";

import { useAuthentication } from "../../src/auth/AuthContext";
import { KeyboardAwareScreen } from "../../src/platform/KeyboardAwareScreen";
import {
  type AchiwaveTheme,
  useAchiwaveTheme,
  useThemeStyles,
} from "../../src/theme/ThemeProvider";
import { AppText } from "../../src/theme/AppText";
import { borders, radii, sizing, spacing, typography } from "../../src/theme/tokens";

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
        <AppText accessibilityRole="header" variant="heading1">
          Account
        </AppText>
        <AppText tone="muted" style={styles.message}>
          Deactivation signs out every device and stops future access. It does not
          permanently delete your retained history.
        </AppText>
        <AppText variant="label" style={styles.label}>Confirm password</AppText>
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
          <AppText
            accessibilityLiveRegion="assertive"
            accessibilityRole="alert"
            tone="error"
            style={styles.error}
          >
            {message}
          </AppText>
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
            <AppText tone="onAction" variant="label">Deactivate account</AppText>
          )}
        </Pressable>
    </KeyboardAwareScreen>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: spacing.lg },
  message: { marginTop: spacing.sm },
  label: { marginTop: spacing.lg },
  input: {
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderRadius: radii.md,
    borderWidth: borders.thin,
    color: theme.colors.foreground,
    ...typography.body,
    marginTop: spacing.xs,
    minHeight: sizing.formControl,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  error: { marginTop: spacing.md },
  dangerButton: {
    alignItems: "center",
    backgroundColor: theme.colors.danger,
    borderRadius: radii.md,
    justifyContent: "center",
    marginTop: spacing.lg,
    minHeight: sizing.formControl,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  dangerButtonPressed: { backgroundColor: theme.colors.dangerPressed },
  disabled: { opacity: 0.65 },
});
