import { Link, Stack, useLocalSearchParams } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
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

export default function ProtectedDetailRoute() {
  const styles = useThemeStyles(createStyles);
  const { section } = useLocalSearchParams<{ section?: string | string[] }>();
  const copy = isRootDestination(section) ? DETAIL_COPY[section] : null;
  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.safeArea}>
      <Stack.Screen options={{ title: copy?.title ?? "Unavailable details" }} />
      <View style={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          {copy?.title ?? "This destination is unavailable"}
        </Text>
        <Text style={styles.description}>
          {copy?.description ?? "The requested protected route is not recognized."}
        </Text>
        {!copy ? (
          <Link href={PROTECTED_ROUTES.home} asChild>
            <Pressable
              accessibilityRole="button"
              style={({ pressed }) => [styles.button, pressed && styles.pressed]}
            >
              <Text style={styles.buttonText}>Return Home</Text>
            </Pressable>
          </Link>
        ) : null}
      </View>
    </SafeAreaView>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: theme.colors.background },
  container: { flex: 1, justifyContent: "center", padding: 24 },
  title: { color: theme.colors.foreground, fontSize: 28, fontWeight: "700", lineHeight: 34 },
  description: { color: theme.colors.foregroundMuted, fontSize: 16, lineHeight: 24, marginTop: 12 },
  button: {
    alignItems: "center",
    alignSelf: "flex-start",
    backgroundColor: theme.colors.action,
    borderRadius: 10,
    justifyContent: "center",
    marginTop: 24,
    minHeight: 48,
    paddingHorizontal: 18,
  },
  pressed: { backgroundColor: theme.colors.actionPressed },
  buttonText: { color: theme.colors.onAction, fontSize: 16, fontWeight: "700" },
});
