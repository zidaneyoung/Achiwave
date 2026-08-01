import { Link, Stack, useLocalSearchParams } from "expo-router";
import { Pressable, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import {
  DETAIL_COPY,
  isRootDestination,
  PROTECTED_ROUTES,
} from "../../../src/navigation/routes";
import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../../../src/theme/ThemeProvider";
import { AppText } from "../../../src/theme/AppText";
import { radii, sizing, spacing } from "../../../src/theme/tokens";

export default function ProtectedDetailRoute() {
  const styles = useThemeStyles(createStyles);
  const { section } = useLocalSearchParams<{ section?: string | string[] }>();
  const copy = isRootDestination(section) ? DETAIL_COPY[section] : null;
  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.safeArea}>
      <Stack.Screen options={{ title: copy?.title ?? "Unavailable details" }} />
      <View style={styles.container}>
        <AppText accessibilityRole="header" variant="heading1">
          {copy?.title ?? "This destination is unavailable"}
        </AppText>
        <AppText tone="muted" style={styles.description}>
          {copy?.description ?? "The requested protected route is not recognized."}
        </AppText>
        {!copy ? (
          <Link href={PROTECTED_ROUTES.home} asChild>
            <Pressable
              accessibilityRole="button"
              style={({ pressed }) => [styles.button, pressed && styles.pressed]}
            >
              <AppText tone="onAction" variant="label">Return Home</AppText>
            </Pressable>
          </Link>
        ) : null}
      </View>
    </SafeAreaView>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: theme.colors.background },
  container: { flex: 1, justifyContent: "center", padding: spacing.lg },
  description: { marginTop: spacing.sm },
  button: {
    alignItems: "center",
    alignSelf: "flex-start",
    backgroundColor: theme.colors.action,
    borderRadius: radii.md,
    justifyContent: "center",
    marginTop: spacing.lg,
    minHeight: sizing.minimumTouchTarget,
    paddingHorizontal: spacing.md,
  },
  pressed: { backgroundColor: theme.colors.actionPressed },
});
