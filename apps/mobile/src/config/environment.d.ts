export type ApiEnvironment = "development" | "test" | "production";

export interface PublicEnvironment {
  apiEnvironment: ApiEnvironment;
  apiBaseUrl: string;
}

export type PublicEnvironmentSource = Record<
  string,
  string | undefined
>;

export function resolvePublicEnvironment(
  source?: PublicEnvironmentSource,
): PublicEnvironment;
