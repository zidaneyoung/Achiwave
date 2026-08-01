import { useCallback, useEffect, useState } from "react";
import { Stack, type ErrorBoundaryProps } from "expo-router";
import { Pressable, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { AuthenticationProvider } from "../src/auth/AuthContext";
import { ReducedMotionProvider } from "../src/accessibility/ReducedMotionProvider";
import { AppSystemBars } from "../src/platform/AppSystemBars";
import { safeConsole } from "../src/security/safeLogging";
import {
  AchiwaveThemeProvider,
  type AchiwaveTheme,
  useAchiwaveTheme,
  useThemeStyles,
} from "../src/theme/ThemeProvider";
import { AppText } from "../src/theme/AppText";
import { radii, sizing, spacing } from "../src/theme/tokens";

export function ErrorBoundary(props: ErrorBoundaryProps) {
  return (
    <AchiwaveThemeProvider>
      <RootErrorBoundary {...props} />
    </AchiwaveThemeProvider>
  );
}

function RootErrorBoundary({ error, retry }: ErrorBoundaryProps) {
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
        <AppText accessibilityRole="header" variant="heading1" style={styles.title}>
          Achiwave needs a moment
        </AppText>
        <AppText tone="muted" style={styles.message}>
          Something unexpected happened. Your details are not shown here.
        </AppText>
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
          <AppText tone="onAction" variant="label">
            {isRetrying ? "Trying again…" : "Try again"}
          </AppText>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

export default function RootLayout() {
  return (
    <AchiwaveThemeProvider>
      <ReducedMotionProvider>
        <ThemedApplication />
      </ReducedMotionProvider>
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
    padding: spacing.lg,
  },
  title: {
    textAlign: "center",
  },
  message: {
    marginTop: spacing.sm,
    maxWidth: 360,
    textAlign: "center",
  },
  button: {
    alignItems: "center",
    backgroundColor: theme.colors.action,
    borderRadius: radii.md,
    justifyContent: "center",
    marginTop: spacing.lg,
    minHeight: sizing.minimumTouchTarget,
    minWidth: 160,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  buttonPressed: {
    backgroundColor: theme.colors.actionPressed,
  },
  buttonDisabled: {
    opacity: 0.65,
  },
});
