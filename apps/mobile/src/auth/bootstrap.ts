import type { AuthenticationState } from "./types";
import { secureCredentialStore } from "./secureCredentials";

export async function bootstrapAuthentication(): Promise<AuthenticationState> {
  const result = await secureCredentialStore.load();
  if (result.status !== "ready") {
    return { status: "unauthenticated" };
  }
  if (Date.parse(result.credentials.sessionExpiresAt) <= Date.now()) {
    await secureCredentialStore.clearAuthentication();
    return { status: "unauthenticated" };
  }
  return { status: "authenticated", user: result.credentials.user };
}
