import { useState } from "react";
import { Link } from "expo-router";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuthentication } from "./AuthContext";
import { AuthenticationRequestError } from "./service";

interface AuthenticationFormProps {
  mode: "login" | "register";
}

export function AuthenticationForm({ mode }: AuthenticationFormProps) {
  const { login, register } = useAuthentication();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
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
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.flex}
      >
        <ScrollView
          contentContainerStyle={styles.container}
          keyboardShouldPersistTaps="handled"
        >
          <Text accessibilityRole="header" style={styles.title}>
            {isRegistration ? "Create your account" : "Welcome back"}
          </Text>
          <Text style={styles.introduction}>
            {isRegistration
              ? "Your credentials stay in Android protected storage."
              : "Sign in to continue to your protected Achiwave account."}
          </Text>

          <View style={styles.field}>
            <Text style={styles.label}>Email</Text>
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
            <Text style={styles.label}>Password</Text>
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
              <Text style={styles.help}>Use at least 12 characters.</Text>
            ) : null}
          </View>

          {errorMessage ? (
            <Text
              accessibilityLiveRegion="assertive"
              accessibilityRole="alert"
              style={styles.error}
            >
              {errorMessage}
            </Text>
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
                color="#ffffff"
              />
            ) : (
              <Text style={styles.primaryButtonText}>
                {isRegistration ? "Create account" : "Sign in"}
              </Text>
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
              <Text style={styles.secondaryButtonText}>
                {isRegistration
                  ? "Already have an account? Sign in"
                  : "Create an account"}
              </Text>
            </Pressable>
          </Link>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#f7f5ef" },
  flex: { flex: 1 },
  container: {
    flexGrow: 1,
    justifyContent: "center",
    padding: 24,
  },
  title: { color: "#17221d", fontSize: 32, fontWeight: "700" },
  introduction: {
    color: "#35423b",
    fontSize: 17,
    lineHeight: 24,
    marginBottom: 16,
    marginTop: 12,
  },
  field: { marginTop: 16 },
  label: { color: "#17221d", fontSize: 17, fontWeight: "600", marginBottom: 8 },
  input: {
    backgroundColor: "#ffffff",
    borderColor: "#66746c",
    borderRadius: 10,
    borderWidth: 1,
    color: "#17221d",
    fontSize: 17,
    minHeight: 52,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  help: { color: "#46534c", fontSize: 15, marginTop: 6 },
  error: { color: "#9f241d", fontSize: 16, lineHeight: 22, marginTop: 16 },
  primaryButton: {
    alignItems: "center",
    backgroundColor: "#1d5b44",
    borderRadius: 10,
    justifyContent: "center",
    marginTop: 24,
    minHeight: 52,
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  primaryButtonPressed: { backgroundColor: "#144432" },
  primaryButtonText: { color: "#ffffff", fontSize: 17, fontWeight: "700" },
  secondaryButton: {
    alignItems: "center",
    borderColor: "#1d5b44",
    borderRadius: 10,
    borderWidth: 2,
    justifyContent: "center",
    marginTop: 16,
    minHeight: 52,
    paddingHorizontal: 18,
    paddingVertical: 12,
  },
  secondaryButtonPressed: { backgroundColor: "#e1ebe5" },
  secondaryButtonText: { color: "#1d5b44", fontSize: 17, fontWeight: "700" },
  disabled: { opacity: 0.65 },
});
