import type { ConfigContext, ExpoConfig } from "expo/config";

import { resolvePublicEnvironment } from "./src/config/environment";

export default function configureExpo({
  config,
}: ConfigContext): ExpoConfig {
  const publicEnvironment = resolvePublicEnvironment();
  if (!config.name || !config.slug) {
    throw new Error("Expo static configuration requires a name and slug.");
  }

  return {
    ...config,
    name: config.name,
    slug: config.slug,
    extra: {
      ...config.extra,
      apiEnvironment: publicEnvironment.apiEnvironment,
      apiBaseUrl: publicEnvironment.apiBaseUrl,
    },
  };
}
