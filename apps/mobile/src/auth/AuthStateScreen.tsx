import { ActivityIndicator, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import {
  type AchiwaveTheme,
  useAchiwaveTheme,
  useThemeStyles,
} from "../theme/ThemeProvider";
import { AppText } from "../theme/AppText";
import { spacing } from "../theme/tokens";

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
        <AppText accessibilityRole="header" variant="heading1" style={styles.title}>
          {title}
        </AppText>
        <AppText tone="muted" style={styles.message}>{message}</AppText>
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
    marginTop: spacing.md,
    textAlign: "center",
  },
  message: {
    marginTop: spacing.sm,
    maxWidth: 380,
    textAlign: "center",
  },
});
