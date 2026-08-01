import { useCallback, useEffect, useState } from "react";
import { Stack, type ErrorBoundaryProps } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { AuthenticationProvider } from "../src/auth/AuthContext";
import { AppSystemBars } from "../src/platform/AppSystemBars";
import { safeConsole } from "../src/security/safeLogging";
import {
  AchiwaveThemeProvider,
  type AchiwaveTheme,
  useAchiwaveTheme,
  useThemeStyles,
} from "../src/theme/ThemeProvider";

export function ErrorBoundary({ error, retry }: ErrorBoundaryProps) {
  const styles = useThemeStyles(createStyles);
  const [isRetrying, setIsRetrying] = useState(false);

  useEffect(() => {
    if (__DEV__) {
      safeConsole.error("root_render_failed");
    }
  }, [error]);

  const handleRetry = useCallback(async () => {
    setIsRetrying(true);
    try {
      await retry();
    } finally {
      setIsRetrying(false);
    }
  }, [retry]);

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.fallback}>
        <Text accessibilityRole="header" style={styles.title}>
          Achiwave needs a moment
        </Text>
        <Text style={styles.message}>
          Something unexpected happened. Your details are not shown here.
        </Text>
        <Pressable
          accessibilityHint="Attempts to display Achiwave again."
          accessibilityRole="button"
          disabled={isRetrying}
          onPress={handleRetry}
          style={({ pressed }) => [
            styles.button,
            pressed && styles.buttonPressed,
            isRetrying && styles.buttonDisabled,
          ]}
        >
          <Text style={styles.buttonText}>
            {isRetrying ? "Trying again…" : "Try again"}
          </Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

export default function RootLayout() {
  return (
    <AchiwaveThemeProvider>
      <ThemedApplication />
    </AchiwaveThemeProvider>
  );
}

function ThemedApplication() {
  const theme = useAchiwaveTheme();
  return (
    <AuthenticationProvider>
      <AppSystemBars />
      <Stack
        screenOptions={{
          contentStyle: { backgroundColor: theme.colors.background },
          headerStyle: { backgroundColor: theme.colors.surface },
          headerTintColor: theme.colors.foreground,
        }}
      >
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
        <Stack.Screen name="(protected)" options={{ headerShown: false }} />
        <Stack.Screen name="+not-found" options={{ title: "Not found" }} />
      </Stack>
    </AuthenticationProvider>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  fallback: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  title: {
    color: theme.colors.foreground,
    fontSize: 28,
    fontWeight: "700",
    textAlign: "center",
  },
  message: {
    color: theme.colors.foregroundMuted,
    fontSize: 17,
    lineHeight: 24,
    marginTop: 12,
    maxWidth: 360,
    textAlign: "center",
  },
  button: {
    alignItems: "center",
    backgroundColor: theme.colors.action,
    borderRadius: 10,
    justifyContent: "center",
    marginTop: 24,
    minHeight: 48,
    minWidth: 160,
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  buttonPressed: {
    backgroundColor: theme.colors.actionPressed,
  },
  buttonDisabled: {
    opacity: 0.65,
  },
  buttonText: {
    color: theme.colors.onAction,
    fontSize: 17,
    fontWeight: "700",
  },
});
