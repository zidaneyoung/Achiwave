import { Link } from "expo-router";
import { Alert, Pressable, StyleSheet } from "react-native";

import { useAuthentication } from "../../../src/auth/AuthContext";
import { RootDestinationScreen } from "../../../src/navigation/RootDestinationScreen";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";
import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../../../src/theme/ThemeProvider";
import { AppText } from "../../../src/theme/AppText";
import { completionQueue } from "../../../src/completions/queue";
import { borders, radii, sizing, spacing } from "../../../src/theme/tokens";

export default function ProfileTabRoute() {
  const styles = useThemeStyles(createStyles);
  const { state, signOut } = useAuthentication();
  if (state.status !== "authenticated") {
    return null;
  }
  async function requestSignOut(): Promise<void> {
    if (state.status !== "authenticated") return;
    let pendingCount: number | null = null;
    try {
      pendingCount = await completionQueue.pendingCount(state.user.id);
    } catch {
      // A storage failure must not skip the safety warning.
    }
    if (pendingCount === 0) {
      await signOut();
      return;
    }
    Alert.alert(
      "Discard pending completions?",
      pendingCount === null
        ? "Pending completion status could not be checked. Signing out clears all queued work on this device."
        : `${pendingCount} pending completion${pendingCount === 1 ? "" : "s"} will be cancelled and removed from this device.`,
      [
        { text: "Keep me signed in", style: "cancel" },
        {
          text: "Discard and sign out",
          style: "destructive",
          onPress: () => void signOut(),
        },
      ],
    );
  }
  return (
    <RootDestinationScreen
      description={state.user.email}
      detailHref={PROTECTED_ROUTES.detail("profile")}
      detailLabel="Open Profile details"
      eyebrow="Account"
      title="Profile"
    >
      <ProfileLink href="/(protected)/security" label="Devices and sessions" styles={styles} />
      <ProfileLink href="/(protected)/preferences" label="Preferences" styles={styles} />
      <ProfileLink href="/(protected)/account" label="Account security" styles={styles} />
      {__DEV__ ? (
        <ProfileLink href={PROTECTED_ROUTES.designSystem} label="Component showcase" styles={styles} />
      ) : null}
      <Pressable
        accessibilityHint="Ends this session and removes local credentials."
        accessibilityRole="button"
        onPress={() => void requestSignOut()}
        style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}
      >
        <AppText variant="label">Sign out</AppText>
      </Pressable>
    </RootDestinationScreen>
  );
}

function ProfileLink({ href, label, styles }: { href: typeof PROTECTED_ROUTES.security | typeof PROTECTED_ROUTES.preferences | typeof PROTECTED_ROUTES.account | typeof PROTECTED_ROUTES.designSystem; label: string; styles: ReturnType<typeof createStyles> }) {
  return (
    <Link href={href} asChild>
      <Pressable
        accessibilityRole="button"
        style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}
      >
        <AppText variant="label">{label}</AppText>
      </Pressable>
    </Link>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  button: {
    alignItems: "center",
    borderColor: theme.colors.borderStrong,
    borderRadius: radii.md,
    borderWidth: borders.thin,
    justifyContent: "center",
    marginTop: spacing.sm,
    minHeight: sizing.minimumTouchTarget,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  buttonPressed: { backgroundColor: theme.colors.surfacePressed },
});
