import { useState } from "react";
import { Link } from "expo-router";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  TextInput,
  View,
} from "react-native";

import { KeyboardAwareScreen } from "../platform/KeyboardAwareScreen";
import {
  type AchiwaveTheme,
  useAchiwaveTheme,
  useThemeStyles,
} from "../theme/ThemeProvider";
import { AppText } from "../theme/AppText";
import { borders, radii, sizing, spacing, typography } from "../theme/tokens";
import { useAuthentication } from "./AuthContext";
import { AuthenticationRequestError } from "./service";

interface AuthenticationFormProps {
  mode: "login" | "register";
}

export function AuthenticationForm({ mode }: AuthenticationFormProps) {
  const theme = useAchiwaveTheme();
  const styles = useThemeStyles(createStyles);
  const { state, login, register } = useAuthentication();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(
    state.status === "unauthenticated" ? (state.message ?? null) : null,
  );
  const [submitting, setSubmitting] = useState(false);
  const isRegistration = mode === "register";

  async function submit(): Promise<void> {
    if (submitting) {
      return;
    }
    if (!email.trim() || !password) {
      setErrorMessage("Enter both your email and password.");
      return;
    }
    if (isRegistration && password.length < 12) {
      setErrorMessage("Create a password with at least 12 characters.");
      return;
    }
    setSubmitting(true);
    setErrorMessage(null);
    try {
      if (isRegistration) {
        await register(email, password);
      } else {
        await login(email, password);
      }
    } catch (error) {
      setErrorMessage(
        error instanceof AuthenticationRequestError
          ? error.message
          : "Authentication could not be completed safely.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <KeyboardAwareScreen contentContainerStyle={styles.container}>
          <AppText accessibilityRole="header" variant="display">
            {isRegistration ? "Create your account" : "Welcome back"}
          </AppText>
          <AppText tone="muted" style={styles.introduction}>
            {isRegistration
              ? "Your credentials stay in Android protected storage."
              : "Sign in to continue to your protected Achiwave account."}
          </AppText>

          <View style={styles.field}>
            <AppText variant="label" style={styles.label}>Email</AppText>
            <TextInput
              accessibilityLabel="Email"
              autoCapitalize="none"
              autoComplete="email"
              editable={!submitting}
              inputMode="email"
              onChangeText={setEmail}
              returnKeyType="next"
              style={styles.input}
              textContentType="emailAddress"
              value={email}
            />
          </View>

          <View style={styles.field}>
            <AppText variant="label" style={styles.label}>Password</AppText>
            <TextInput
              accessibilityLabel="Password"
              autoCapitalize="none"
              autoComplete={isRegistration ? "new-password" : "current-password"}
              editable={!submitting}
              onChangeText={setPassword}
              onSubmitEditing={() => void submit()}
              returnKeyType="done"
              secureTextEntry
              style={styles.input}
              textContentType={isRegistration ? "newPassword" : "password"}
              value={password}
            />
            {isRegistration ? (
              <AppText tone="subtle" variant="caption" style={styles.help}>Use at least 12 characters.</AppText>
            ) : null}
          </View>

          {errorMessage ? (
            <AppText
              accessibilityLiveRegion="assertive"
              accessibilityRole="alert"
              tone="error"
              style={styles.error}
            >
              {errorMessage}
            </AppText>
          ) : null}

          <Pressable
            accessibilityHint={
              isRegistration
                ? "Creates your protected Achiwave account."
                : "Signs in to your Achiwave account."
            }
            accessibilityRole="button"
            disabled={submitting}
            onPress={() => void submit()}
            style={({ pressed }) => [
              styles.primaryButton,
              pressed && styles.primaryButtonPressed,
              submitting && styles.disabled,
            ]}
          >
            {submitting ? (
              <ActivityIndicator
                accessibilityLabel="Authentication in progress"
                color={theme.colors.onAction}
              />
            ) : (
              <AppText tone="onAction" variant="label">
                {isRegistration ? "Create account" : "Sign in"}
              </AppText>
            )}
          </Pressable>

          <Link
            href={isRegistration ? "/(auth)/login" : "/(auth)/register"}
            asChild
          >
            <Pressable
              accessibilityRole="button"
              disabled={submitting}
              style={({ pressed }) => [
                styles.secondaryButton,
                pressed && styles.secondaryButtonPressed,
              ]}
            >
              <AppText variant="label">
                {isRegistration
                  ? "Already have an account? Sign in"
                  : "Create an account"}
              </AppText>
            </Pressable>
          </Link>
    </KeyboardAwareScreen>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  container: {
    flexGrow: 1,
    justifyContent: "center",
    padding: spacing.lg,
  },
  introduction: {
    marginBottom: spacing.md,
    marginTop: spacing.sm,
  },
  field: { marginTop: spacing.md },
  label: { marginBottom: spacing.xs },
  input: {
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderRadius: radii.md,
    borderWidth: borders.thin,
    color: theme.colors.foreground,
    ...typography.body,
    minHeight: sizing.formControl,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  help: { marginTop: spacing.xs },
  error: { marginTop: spacing.md },
  primaryButton: {
    alignItems: "center",
    backgroundColor: theme.colors.action,
    borderRadius: radii.md,
    justifyContent: "center",
    marginTop: spacing.lg,
    minHeight: sizing.formControl,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  primaryButtonPressed: { backgroundColor: theme.colors.actionPressed },
  secondaryButton: {
    alignItems: "center",
    borderColor: theme.colors.borderStrong,
    borderRadius: radii.md,
    borderWidth: borders.selected,
    justifyContent: "center",
    marginTop: spacing.md,
    minHeight: sizing.formControl,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  secondaryButtonPressed: { backgroundColor: theme.colors.surfacePressed },
  disabled: { opacity: 0.65 },
});
