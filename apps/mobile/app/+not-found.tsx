import { Link } from "expo-router";
import { StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../src/theme/ThemeProvider";
import { AppText } from "../src/theme/AppText";
import { spacing, typography } from "../src/theme/tokens";

export default function NotFoundRoute() {
  const styles = useThemeStyles(createStyles);
  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.safeArea}>
      <View style={styles.container}>
        <AppText accessibilityRole="header" variant="heading2" style={styles.title}>
          This route does not exist.
        </AppText>
        <Link accessibilityRole="link" href="/" style={styles.link}>
          Return to Achiwave
        </Link>
      </View>
    </SafeAreaView>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.lg,
  },
  title: {
    textAlign: "center",
  },
  link: {
    color: theme.colors.action,
    ...typography.body,
    marginTop: spacing.md,
    textDecorationLine: "underline",
  },
});
