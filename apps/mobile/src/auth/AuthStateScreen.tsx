import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import {
  type AchiwaveTheme,
  useAchiwaveTheme,
  useThemeStyles,
} from "../theme/ThemeProvider";

interface AuthStateScreenProps {
  title: string;
  message: string;
  loading?: boolean;
}

export function AuthStateScreen({
  title,
  message,
  loading = false,
}: AuthStateScreenProps) {
  const theme = useAchiwaveTheme();
  const styles = useThemeStyles(createStyles);
  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        {loading ? (
          <ActivityIndicator
            accessibilityLabel="Checking authentication"
            color={theme.colors.accent}
            size="large"
          />
        ) : null}
        <Text accessibilityRole="header" style={styles.title}>
          {title}
        </Text>
        <Text style={styles.message}>{message}</Text>
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
    fontSize: 28,
    fontWeight: "700",
    marginTop: 16,
    textAlign: "center",
  },
  message: {
    color: theme.colors.foregroundMuted,
    fontSize: 17,
    lineHeight: 24,
    marginTop: 12,
    maxWidth: 380,
    textAlign: "center",
  },
});
