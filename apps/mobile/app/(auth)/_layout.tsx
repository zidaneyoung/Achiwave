import { Redirect, Stack } from "expo-router";

import { AuthStateScreen } from "../../src/auth/AuthStateScreen";
import { useAuthentication } from "../../src/auth/AuthContext";

export default function AuthenticationLayout() {
  const { state } = useAuthentication();
  if (state.status === "loading") {
    return (
      <AuthStateScreen
        loading
        message="Your session is being checked."
        title="Checking your session"
      />
    );
  }
  if (state.status === "authenticated") {
    return <Redirect href="/(protected)" />;
  }
  if (state.status === "offline_limited") {
    return <Redirect href="/(protected)/offline" />;
  }
  return (
    <Stack>
      <Stack.Screen name="login" options={{ title: "Sign in" }} />
      <Stack.Screen name="register" options={{ title: "Create account" }} />
    </Stack>
  );
}
