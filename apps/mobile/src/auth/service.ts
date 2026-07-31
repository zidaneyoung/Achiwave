import Constants from "expo-constants";

import { getRuntimeEnvironment } from "../config/runtime";
import {
  secureCredentialStore,
  type AuthenticationCredentials,
  type SecureCredentialStore,
} from "./secureCredentials";
import type { AuthenticatedUserSnapshot, AuthenticationState } from "./types";

const PERMANENT_SESSION_CODES = new Set([
  "account_deactivated",
  "device_revoked",
  "invalid_access_token",
  "invalid_refresh_token",
  "refresh_token_reuse_detected",
  "session_expired",
  "session_revoked",
]);

export type AuthenticationErrorCode =
  | "email_already_registered"
  | "invalid_credentials"
  | "session_rejected"
  | "storage_unavailable"
  | "unavailable"
  | "validation_error"
  | "unexpected_response";

export class AuthenticationRequestError extends Error {
  constructor(
    public readonly code: AuthenticationErrorCode,
    message: string,
  ) {
    super(message);
    this.name = "AuthenticationRequestError";
  }
}

interface AuthenticationInput {
  email: string;
  password: string;
}

interface AuthenticationServiceOptions {
  baseUrl?: string;
  apiEnvironment?: "development" | "test" | "production";
  credentialStore?: SecureCredentialStore;
  fetchImplementation?: typeof fetch;
  timeoutMilliseconds?: number;
}

interface AuthenticationResponsePayload {
  user: AuthenticatedUserSnapshot;
  deviceId: string;
  sessionId: string;
  sessionExpiresAt: string;
  accessToken: string;
  accessTokenExpiresAt: string;
  refreshToken: string;
}

interface RefreshResponsePayload {
  sessionId: string;
  sessionExpiresAt: string;
  accessToken: string;
  accessTokenExpiresAt: string;
  refreshToken: string;
}

interface ApiErrorPayload {
  code: string;
}

export interface AuthenticationService {
  register(input: AuthenticationInput): Promise<AuthenticatedUserSnapshot>;
  login(input: AuthenticationInput): Promise<AuthenticatedUserSnapshot>;
  restore(): Promise<AuthenticationState>;
  logout(): Promise<void>;
  request(path: string, init?: RequestInit): Promise<Response>;
  subscribeSessionRejected(listener: () => void): () => void;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function readString(
  source: Record<string, unknown>,
  snakeCase: string,
): string | null {
  const value = source[snakeCase];
  return typeof value === "string" && value.length > 0 ? value : null;
}

function parseAuthenticationPayload(
  value: unknown,
): AuthenticationResponsePayload | null {
  if (!isObject(value) || !isObject(value.user)) {
    return null;
  }
  const userId = readString(value.user, "id");
  const email = readString(value.user, "email");
  const deviceId = readString(value, "device_id");
  const sessionId = readString(value, "session_id");
  const sessionExpiresAt = readString(value, "session_expires_at");
  const accessToken = readString(value, "access_token");
  const accessTokenExpiresAt = readString(value, "access_token_expires_at");
  const refreshToken = readString(value, "refresh_token");
  if (
    !userId ||
    !email ||
    !deviceId ||
    !sessionId ||
    !sessionExpiresAt ||
    !accessToken ||
    !accessTokenExpiresAt ||
    !refreshToken
  ) {
    return null;
  }
  return {
    user: { id: userId, email },
    deviceId,
    sessionId,
    sessionExpiresAt,
    accessToken,
    accessTokenExpiresAt,
    refreshToken,
  };
}

function parseRefreshPayload(value: unknown): RefreshResponsePayload | null {
  if (!isObject(value)) {
    return null;
  }
  const sessionId = readString(value, "session_id");
  const sessionExpiresAt = readString(value, "session_expires_at");
  const accessToken = readString(value, "access_token");
  const accessTokenExpiresAt = readString(value, "access_token_expires_at");
  const refreshToken = readString(value, "refresh_token");
  if (
    !sessionId ||
    !sessionExpiresAt ||
    !accessToken ||
    !accessTokenExpiresAt ||
    !refreshToken
  ) {
    return null;
  }
  return {
    sessionId,
    sessionExpiresAt,
    accessToken,
    accessTokenExpiresAt,
    refreshToken,
  };
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function parseApiError(value: unknown): ApiErrorPayload | null {
  if (!isObject(value)) {
    return null;
  }
  const code = readString(value, "code");
  return code ? { code } : null;
}

function userFacingError(code: string | null): AuthenticationRequestError {
  if (code === "invalid_credentials" || code === "account_deactivated") {
    return new AuthenticationRequestError(
      "invalid_credentials",
      "The email or password was not accepted.",
    );
  }
  if (code === "email_already_registered") {
    return new AuthenticationRequestError(
      "email_already_registered",
      "An account already uses that email address.",
    );
  }
  if (code === "validation_error") {
    return new AuthenticationRequestError(
      "validation_error",
      "Check the entered values and try again.",
    );
  }
  return new AuthenticationRequestError(
    "unexpected_response",
    "Achiwave returned an unexpected response.",
  );
}

export function createAuthenticationService({
  baseUrl = getRuntimeEnvironment().apiBaseUrl,
  apiEnvironment = getRuntimeEnvironment().apiEnvironment,
  credentialStore = secureCredentialStore,
  fetchImplementation = fetch,
  timeoutMilliseconds = 10_000,
}: AuthenticationServiceOptions = {}): AuthenticationService {
  let refreshPromise: Promise<AuthenticationCredentials> | null = null;
  const sessionRejectedListeners = new Set<() => void>();
  const appEnvironment =
    apiEnvironment === "test" ? "preview" : apiEnvironment;

  async function fetchApi(path: string, init: RequestInit): Promise<Response> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMilliseconds);
    try {
      return await fetchImplementation(`${baseUrl}${path}`, {
        ...init,
        headers: {
          Accept: "application/json",
          ...init.headers,
        },
        signal: controller.signal,
      });
    } catch {
      throw new AuthenticationRequestError(
        "unavailable",
        "Achiwave is unavailable. Check your connection and try again.",
      );
    } finally {
      clearTimeout(timeout);
    }
  }

  async function installationPayload(): Promise<Record<string, unknown>> {
    const installationId = await credentialStore.getOrCreateInstallationId();
    return {
      installation_id: installationId,
      platform: "android",
      app_environment: appEnvironment,
      app_version: Constants.expoConfig?.version,
      build_version: Constants.expoConfig?.android?.versionCode?.toString(),
    };
  }

  async function storeAuthentication(
    payload: AuthenticationResponsePayload,
  ): Promise<AuthenticatedUserSnapshot> {
    await credentialStore.save({
      accessToken: payload.accessToken,
      accessTokenExpiresAt: payload.accessTokenExpiresAt,
      refreshToken: payload.refreshToken,
      sessionId: payload.sessionId,
      sessionExpiresAt: payload.sessionExpiresAt,
      deviceId: payload.deviceId,
      user: payload.user,
    });
    return payload.user;
  }

  async function authenticate(
    endpoint: "login" | "register",
    input: AuthenticationInput,
  ): Promise<AuthenticatedUserSnapshot> {
    const response = await fetchApi(`/api/v1/auth/${endpoint}`, {
      body: JSON.stringify({
        email: input.email.trim(),
        password: input.password,
        installation: await installationPayload(),
      }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
    const body = await readJson(response);
    if (!response.ok) {
      throw userFacingError(parseApiError(body)?.code ?? null);
    }
    const payload = parseAuthenticationPayload(body);
    if (!payload) {
      throw userFacingError(null);
    }
    return storeAuthentication(payload);
  }

  async function performRefresh(
    expectedSessionId: string,
  ): Promise<AuthenticationCredentials> {
    const currentResult = await credentialStore.load();
    if (currentResult.status !== "ready") {
      throw new AuthenticationRequestError(
        "session_rejected",
        "Your session is no longer available. Sign in again.",
      );
    }
    if (currentResult.credentials.sessionId !== expectedSessionId) {
      return currentResult.credentials;
    }
    const response = await fetchApi("/api/v1/auth/refresh", {
      body: JSON.stringify({
        refresh_token: currentResult.credentials.refreshToken,
        installation: await installationPayload(),
      }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
    const body = await readJson(response);
    if (!response.ok) {
      const errorCode = parseApiError(body)?.code ?? null;
      if (response.status === 401 || (errorCode && PERMANENT_SESSION_CODES.has(errorCode))) {
        await rejectSession();
        throw new AuthenticationRequestError(
          "session_rejected",
          "Your session ended. Sign in again.",
        );
      }
      throw userFacingError(errorCode);
    }
    const refreshed = parseRefreshPayload(body);
    if (!refreshed) {
      throw userFacingError(null);
    }
    const credentials: AuthenticationCredentials = {
      ...currentResult.credentials,
      ...refreshed,
    };
    await credentialStore.save(credentials);
    return credentials;
  }

  function refresh(
    expectedSessionId: string,
  ): Promise<AuthenticationCredentials> {
    if (refreshPromise === null) {
      refreshPromise = performRefresh(expectedSessionId).finally(() => {
        refreshPromise = null;
      });
    }
    return refreshPromise;
  }

  async function rejectSession(): Promise<void> {
    await credentialStore.clearAuthentication();
    for (const listener of sessionRejectedListeners) {
      listener();
    }
  }

  async function requestWithAccessToken(
    path: string,
    init: RequestInit,
    accessToken: string,
  ): Promise<Response> {
    return fetchApi(path, {
      ...init,
      headers: {
        ...init.headers,
        Authorization: `Bearer ${accessToken}`,
      },
    });
  }

  return {
    register(input) {
      return authenticate("register", input);
    },

    login(input) {
      return authenticate("login", input);
    },

    async restore(): Promise<AuthenticationState> {
      const result = await credentialStore.load();
      if (result.status !== "ready") {
        return { status: "unauthenticated" };
      }
      if (Date.parse(result.credentials.sessionExpiresAt) <= Date.now()) {
        await credentialStore.clearAuthentication();
        return { status: "unauthenticated" };
      }
      try {
        const credentials = await refresh(result.credentials.sessionId);
        return { status: "authenticated", user: credentials.user };
      } catch (error) {
        if (
          error instanceof AuthenticationRequestError &&
          error.code === "unavailable"
        ) {
          return { status: "offline_limited", user: result.credentials.user };
        }
        if (
          error instanceof AuthenticationRequestError &&
          error.code === "session_rejected"
        ) {
          return { status: "unauthenticated" };
        }
        throw error;
      }
    },

    async logout(): Promise<void> {
      const result = await credentialStore.load();
      try {
        if (result.status === "ready") {
          await fetchApi("/api/v1/auth/logout", {
            body: JSON.stringify({
              refresh_token: result.credentials.refreshToken,
            }),
            headers: {
              Authorization: `Bearer ${result.credentials.accessToken}`,
              "Content-Type": "application/json",
            },
            method: "POST",
          });
        }
      } finally {
        await credentialStore.clearAuthentication();
      }
    },

    async request(path: string, init: RequestInit = {}): Promise<Response> {
      const result = await credentialStore.load();
      if (result.status !== "ready") {
        throw new AuthenticationRequestError(
          "session_rejected",
          "Your session is no longer available. Sign in again.",
        );
      }
      let credentials = result.credentials;
      if (Date.parse(credentials.accessTokenExpiresAt) <= Date.now() + 30_000) {
        credentials = await refresh(credentials.sessionId);
      }
      let response = await requestWithAccessToken(
        path,
        init,
        credentials.accessToken,
      );
      if (response.status !== 401) {
        return response;
      }
      credentials = await refresh(credentials.sessionId);
      response = await requestWithAccessToken(path, init, credentials.accessToken);
      if (response.status === 401) {
        await rejectSession();
        throw new AuthenticationRequestError(
          "session_rejected",
          "Your session ended. Sign in again.",
        );
      }
      return response;
    },

    subscribeSessionRejected(listener: () => void): () => void {
      sessionRejectedListeners.add(listener);
      return () => sessionRejectedListeners.delete(listener);
    },
  };
}

export const authenticationService = createAuthenticationService();
