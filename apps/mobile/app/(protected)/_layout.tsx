import { Redirect, Stack } from "expo-router";

import { AuthStateScreen } from "../../src/auth/AuthStateScreen";
import { useAuthentication } from "../../src/auth/AuthContext";

export default function ProtectedLayout() {
  const { state } = useAuthentication();
  if (state.status === "loading") {
    return (
      <AuthStateScreen
        loading
        message="Protected content stays hidden until your session is checked."
        title="Checking your session"
      />
    );
  }
  if (state.status === "unauthenticated") {
    return <Redirect href="/(auth)/login" />;
  }
  if (state.status === "failure") {
    return <AuthStateScreen message={state.message} title="Session unavailable" />;
  }
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Achiwave" }} />
      <Stack.Screen name="offline" options={{ title: "Offline" }} />
      <Stack.Screen name="security" options={{ title: "Devices and sessions" }} />
      <Stack.Screen name="preferences" options={{ title: "Preferences" }} />
    </Stack>
  );
}
