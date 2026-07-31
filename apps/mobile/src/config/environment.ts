export type ApiEnvironment = "development" | "test" | "production";

export interface PublicEnvironment {
  apiEnvironment: ApiEnvironment;
  apiBaseUrl: string;
}

type PublicEnvironmentSource = Record<string, string | undefined>;

const API_ENVIRONMENTS = new Set<ApiEnvironment>([
  "development",
  "test",
  "production",
]);

export function resolvePublicEnvironment(
  source: PublicEnvironmentSource = process.env,
): PublicEnvironment {
  const apiEnvironment = source.EXPO_PUBLIC_API_ENV;
  if (!API_ENVIRONMENTS.has(apiEnvironment as ApiEnvironment)) {
    throw new Error(
      "EXPO_PUBLIC_API_ENV must be development, test, or production.",
    );
  }

  const apiBaseUrl = source.EXPO_PUBLIC_API_BASE_URL?.trim();
  if (!apiBaseUrl) {
    throw new Error("EXPO_PUBLIC_API_BASE_URL is required.");
  }

  const parsedUrl = new URL(apiBaseUrl);
  if (parsedUrl.protocol !== "http:" && parsedUrl.protocol !== "https:") {
    throw new Error("EXPO_PUBLIC_API_BASE_URL must use HTTP or HTTPS.");
  }

  return {
    apiEnvironment: apiEnvironment as ApiEnvironment,
    apiBaseUrl: apiBaseUrl.replace(/\/+$/, ""),
  };
}
