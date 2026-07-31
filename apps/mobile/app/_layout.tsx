import { useCallback, useEffect, useState } from "react";
import { Stack, type ErrorBoundaryProps } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export function ErrorBoundary({ error, retry }: ErrorBoundaryProps) {
  const [isRetrying, setIsRetrying] = useState(false);

  useEffect(() => {
    if (__DEV__) {
      console.error("Achiwave root render failed.");
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
    <Stack>
      <Stack.Screen name="index" options={{ title: "Achiwave" }} />
      <Stack.Screen name="+not-found" options={{ title: "Not found" }} />
    </Stack>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#f7f5ef",
  },
  fallback: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  title: {
    color: "#17221d",
    fontSize: 28,
    fontWeight: "700",
    textAlign: "center",
  },
  message: {
    color: "#35423b",
    fontSize: 17,
    lineHeight: 24,
    marginTop: 12,
    maxWidth: 360,
    textAlign: "center",
  },
  button: {
    alignItems: "center",
    backgroundColor: "#1d5b44",
    borderRadius: 10,
    justifyContent: "center",
    marginTop: 24,
    minHeight: 48,
    minWidth: 160,
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  buttonPressed: {
    backgroundColor: "#144432",
  },
  buttonDisabled: {
    opacity: 0.65,
  },
  buttonText: {
    color: "#ffffff",
    fontSize: 17,
    fontWeight: "700",
  },
});
