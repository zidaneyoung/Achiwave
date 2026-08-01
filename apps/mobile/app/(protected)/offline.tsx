import { Pressable, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuthentication } from "../../src/auth/AuthContext";
import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../../src/theme/ThemeProvider";
import { AppText } from "../../src/theme/AppText";
import { radii, sizing, spacing } from "../../src/theme/tokens";

export default function OfflineLimitedRoute() {
  const { revalidate } = useAuthentication();
  const styles = useThemeStyles(createStyles);

  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.safeArea}>
      <View style={styles.container}>
        <AppText accessibilityRole="header" variant="heading1" style={styles.title}>
          You are offline
        </AppText>
        <AppText tone="muted" style={styles.message}>
          A previously confirmed session is present, but no private feature data is
          available for offline use yet. Reconnect before making changes.
        </AppText>
        <Pressable
          accessibilityHint="Checks the saved session with the Achiwave service."
          accessibilityRole="button"
          onPress={() => void revalidate()}
          style={({ pressed }) => [
            styles.button,
            pressed && styles.buttonPressed,
          ]}
        >
          <AppText tone="onAction" variant="label">Check connection</AppText>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: theme.colors.background },
  container: { flex: 1, justifyContent: "center", padding: spacing.lg },
  title: { textAlign: "center" },
  message: {
    marginTop: spacing.sm,
    textAlign: "center",
  },
  button: {
    alignItems: "center",
    backgroundColor: theme.colors.action,
    borderRadius: radii.md,
    justifyContent: "center",
    marginTop: spacing.lg,
    minHeight: sizing.formControl,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  buttonPressed: { backgroundColor: theme.colors.actionPressed },
});
