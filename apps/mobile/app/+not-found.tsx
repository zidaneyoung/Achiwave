import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../src/theme/ThemeProvider";

export default function NotFoundRoute() {
  const styles = useThemeStyles(createStyles);
  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.safeArea}>
      <View style={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          This route does not exist.
        </Text>
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
    padding: 24,
  },
  title: {
    color: theme.colors.foreground,
    fontSize: 24,
    fontWeight: "700",
    textAlign: "center",
  },
  link: {
    color: theme.colors.action,
    fontSize: 17,
    marginTop: 20,
    textDecorationLine: "underline",
  },
});
