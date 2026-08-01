import { Link } from "expo-router";
import { Pressable, StyleSheet } from "react-native";

import { RootDestinationScreen } from "../../../src/navigation/RootDestinationScreen";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";
import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../../../src/theme/ThemeProvider";
import { AppText } from "../../../src/theme/AppText";
import { borders, radii, sizing, spacing } from "../../../src/theme/tokens";

export default function HomeTabRoute() {
  const styles = useThemeStyles(createStyles);
  return (
    <RootDestinationScreen
      description="Your focused starting point for daily progress. Stage 6 will connect authoritative campaign and quest data."
      detailHref={PROTECTED_ROUTES.detail("home")}
      detailLabel="Open Home details"
      eyebrow="Daily command"
      title="Welcome to Achiwave"
    >
      <Link href={PROTECTED_ROUTES.modal} asChild>
        <Pressable
          accessibilityHint="Opens a temporary protected modal."
          accessibilityRole="button"
          style={({ pressed }) => [styles.button, pressed && styles.pressed]}
        >
          <AppText variant="label">Open modal example</AppText>
        </Pressable>
      </Link>
    </RootDestinationScreen>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  button: {
    alignItems: "center",
    borderColor: theme.colors.borderStrong,
    borderRadius: radii.md,
    borderWidth: borders.thin,
    justifyContent: "center",
    minHeight: sizing.minimumTouchTarget,
    paddingHorizontal: spacing.md,
  },
  pressed: { backgroundColor: theme.colors.surfacePressed },
});
