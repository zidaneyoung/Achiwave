import type { AuthenticationState } from "./types";
import { authenticationService } from "./service";

export async function bootstrapAuthentication(): Promise<AuthenticationState> {
  return authenticationService.restore();
}
