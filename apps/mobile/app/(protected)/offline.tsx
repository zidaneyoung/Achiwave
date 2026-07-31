import { AuthStateScreen } from "../../src/auth/AuthStateScreen";

export default function OfflineLimitedRoute() {
  return (
    <AuthStateScreen
      message="A previously confirmed session is available for limited read-only use. Reconnect before making changes."
      title="You are offline"
    />
  );
}
