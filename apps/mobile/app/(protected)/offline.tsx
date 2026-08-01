import { Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuthentication } from "../../src/auth/AuthContext";
import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../../src/theme/ThemeProvider";

export default function OfflineLimitedRoute() {
  const { revalidate } = useAuthentication();
  const styles = useThemeStyles(createStyles);

  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.safeArea}>
      <View style={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          You are offline
        </Text>
        <Text style={styles.message}>
          A previously confirmed session is present, but no private feature data is
          available for offline use yet. Reconnect before making changes.
        </Text>
        <Pressable
          accessibilityHint="Checks the saved session with the Achiwave service."
          accessibilityRole="button"
          onPress={() => void revalidate()}
          style={({ pressed }) => [
            styles.button,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.buttonText}>Check connection</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: theme.colors.background },
  container: { flex: 1, justifyContent: "center", padding: 24 },
  title: { color: theme.colors.foreground, fontSize: 30, fontWeight: "700", textAlign: "center" },
  message: {
    color: theme.colors.foregroundMuted,
    fontSize: 17,
    lineHeight: 24,
    marginTop: 12,
    textAlign: "center",
  },
  button: {
    alignItems: "center",
    backgroundColor: theme.colors.action,
    borderRadius: 10,
    justifyContent: "center",
    marginTop: 24,
    minHeight: 52,
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  buttonPressed: { backgroundColor: theme.colors.actionPressed },
  buttonText: { color: theme.colors.onAction, fontSize: 17, fontWeight: "700" },
});
