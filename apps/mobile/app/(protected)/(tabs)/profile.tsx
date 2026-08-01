import { Link } from "expo-router";
import { Pressable, StyleSheet, Text } from "react-native";

import { useAuthentication } from "../../../src/auth/AuthContext";
import { RootDestinationScreen } from "../../../src/navigation/RootDestinationScreen";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";

export default function ProfileTabRoute() {
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
      <ProfileLink href="/(protected)/security" label="Devices and sessions" />
      <ProfileLink href="/(protected)/preferences" label="Preferences" />
      <ProfileLink href="/(protected)/account" label="Account security" />
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

function ProfileLink({ href, label }: { href: typeof PROTECTED_ROUTES.security | typeof PROTECTED_ROUTES.preferences | typeof PROTECTED_ROUTES.account; label: string }) {
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

const styles = StyleSheet.create({
  button: {
    alignItems: "center",
    borderColor: "#66C0F4",
    borderRadius: 10,
    borderWidth: 1,
    justifyContent: "center",
    marginTop: 12,
    minHeight: 48,
    paddingHorizontal: 18,
    paddingVertical: 12,
  },
  buttonPressed: { backgroundColor: "#2A475E" },
  buttonText: { color: "#C7D5E0", fontSize: 16, fontWeight: "700" },
});
