import { Link } from "expo-router";
import { Pressable, StyleSheet, Text } from "react-native";

import { RootDestinationScreen } from "../../../src/navigation/RootDestinationScreen";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";

export default function HomeTabRoute() {
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
          <Text style={styles.buttonText}>Open modal example</Text>
        </Pressable>
      </Link>
    </RootDestinationScreen>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: "center",
    borderColor: "#66C0F4",
    borderRadius: 10,
    borderWidth: 1,
    justifyContent: "center",
    minHeight: 48,
    paddingHorizontal: 18,
  },
  pressed: { backgroundColor: "#2A475E" },
  buttonText: { color: "#C7D5E0", fontSize: 16, fontWeight: "700" },
});
