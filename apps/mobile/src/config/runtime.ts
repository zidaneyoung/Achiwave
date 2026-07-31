import Constants from "expo-constants";

import type { PublicEnvironment } from "./environment";

export function getRuntimeEnvironment(): PublicEnvironment {
  const extra = Constants.expoConfig?.extra;
  const apiEnvironment = extra?.apiEnvironment;
  const apiBaseUrl = extra?.apiBaseUrl;
  if (
    (apiEnvironment !== "development" &&
      apiEnvironment !== "test" &&
      apiEnvironment !== "production") ||
    typeof apiBaseUrl !== "string" ||
    apiBaseUrl.length === 0
  ) {
    throw new Error("The public application environment is unavailable.");
  }
  return { apiEnvironment, apiBaseUrl };
}
