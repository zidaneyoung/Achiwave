export type AuthenticationStatus =
  | "loading"
  | "authenticated"
  | "unauthenticated"
  | "offline_limited"
  | "failure";

export interface AuthenticatedUserSnapshot {
  id: string;
  email: string;
}

export type AuthenticationState =
  | { status: "loading" }
  | { status: "authenticated"; user: AuthenticatedUserSnapshot }
  | { status: "unauthenticated"; message?: string }
  | { status: "offline_limited"; user: AuthenticatedUserSnapshot }
  | { status: "failure"; message: string };
