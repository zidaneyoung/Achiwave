import type { AuthenticationState } from "./types";

export async function bootstrapAuthentication(): Promise<AuthenticationState> {
  return { status: "unauthenticated" };
}
