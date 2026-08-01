import { Redirect } from "expo-router";

import { PROTECTED_ROUTES } from "../../src/navigation/routes";

export default function ProtectedHomeRoute() {
  return <Redirect href={PROTECTED_ROUTES.home} />;
}
