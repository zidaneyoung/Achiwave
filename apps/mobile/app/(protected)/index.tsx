import { Redirect } from "expo-router";

export default function ProtectedHomeRoute() {
  return <Redirect href="/(protected)/(tabs)/home" />;
}
