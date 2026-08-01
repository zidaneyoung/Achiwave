import { Link } from "expo-router";
import { Pressable, StyleSheet, Text } from "react-native";

import { useAuthentication } from "../../../src/auth/AuthContext";
import { RootDestinationScreen } from "../../../src/navigation/RootDestinationScreen";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";
import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../../../src/theme/ThemeProvider";

export default function ProfileTabRoute() {
  const styles = useThemeStyles(createStyles);
  const { state, signOut } = useAuthentication();
  if (state.status !== "authenticated") {
    return null;
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
      <Pressable
        accessibilityHint="Ends this session and removes local credentials."
        accessibilityRole="button"
        onPress={() => void signOut()}
        style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}
      >
        <Text style={styles.buttonText}>Sign out</Text>
      </Pressable>
    </RootDestinationScreen>
  );
}

function ProfileLink({ href, label, styles }: { href: typeof PROTECTED_ROUTES.security | typeof PROTECTED_ROUTES.preferences | typeof PROTECTED_ROUTES.account; label: string; styles: ReturnType<typeof createStyles> }) {
  return (
    <Link href={href} asChild>
      <Pressable
        accessibilityRole="button"
        style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}
      >
        <Text style={styles.buttonText}>{label}</Text>
      </Pressable>
    </Link>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  button: {
    alignItems: "center",
    borderColor: theme.colors.borderStrong,
    borderRadius: 10,
    borderWidth: 1,
    justifyContent: "center",
    marginTop: 12,
    minHeight: 48,
    paddingHorizontal: 18,
    paddingVertical: 12,
  },
  buttonPressed: { backgroundColor: theme.colors.surfacePressed },
  buttonText: { color: theme.colors.foreground, fontSize: 16, fontWeight: "700" },
});
