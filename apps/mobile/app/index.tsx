import { Redirect } from "expo-router";

import { AuthStateScreen } from "../src/auth/AuthStateScreen";
import { useAuthentication } from "../src/auth/AuthContext";

export default function EntryRoute() {
  const { state } = useAuthentication();
  if (state.status === "loading") {
    return (
      <AuthStateScreen
        loading
        message="Your protected session is being checked before anything private is shown."
        title="Checking your session"
      />
    );
  }
  if (state.status === "failure") {
    return <AuthStateScreen message={state.message} title="Sign-in unavailable" />;
  }
  if (state.status === "authenticated") {
    return <Redirect href="/(protected)" />;
  }
  if (state.status === "offline_limited") {
    return <Redirect href="/(protected)/offline" />;
  }
  return <Redirect href="/(auth)/login" />;
}
