import { Redirect, Stack, useSegments } from "expo-router";

import { AuthStateScreen } from "../../src/auth/AuthStateScreen";
import { useAuthentication } from "../../src/auth/AuthContext";
import { useAchiwaveTheme } from "../../src/theme/ThemeProvider";

export const unstable_settings = {
  initialRouteName: "(tabs)",
};

export default function ProtectedLayout() {
  const { state } = useAuthentication();
  const theme = useAchiwaveTheme();
  const segments = useSegments();
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
  if (
    state.status === "offline_limited" &&
    segments[segments.length - 1] !== "offline"
  ) {
    return <Redirect href="/(protected)/offline" />;
  }
  return (
    <Stack
      initialRouteName="(tabs)"
      screenOptions={{
        animation: "slide_from_right",
        contentStyle: { backgroundColor: theme.colors.background },
        headerBackButtonDisplayMode: "minimal",
        headerStyle: { backgroundColor: theme.colors.surface },
        headerTintColor: theme.colors.foreground,
      }}
    >
      <Stack.Screen name="index" options={{ headerShown: false }} />
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="details/[section]" options={{ title: "Details" }} />
      <Stack.Screen
        name="modal"
        options={{
          animation: "slide_from_bottom",
          headerShown: false,
          presentation: "modal",
        }}
      />
      <Stack.Screen name="offline" options={{ title: "Offline" }} />
      <Stack.Screen name="security" options={{ title: "Devices and sessions" }} />
      <Stack.Screen name="preferences" options={{ title: "Preferences" }} />
      <Stack.Screen name="account" options={{ title: "Account" }} />
    </Stack>
  );
}
