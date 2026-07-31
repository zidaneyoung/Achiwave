import * as SecureStore from "expo-secure-store";

import type { ApiEnvironment } from "../config/environment";
import { getRuntimeEnvironment } from "../config/runtime";
import type { AuthenticatedUserSnapshot } from "./types";

const CREDENTIAL_VERSION = 1;
const SECURE_STORE_OPTIONS: SecureStore.SecureStoreOptions = {
  requireAuthentication: false,
};

export interface AuthenticationCredentials {
  accessToken: string;
  accessTokenExpiresAt: string;
  refreshToken: string;
  sessionId: string;
  sessionExpiresAt: string;
  deviceId: string;
  user: AuthenticatedUserSnapshot;
}

interface StoredAuthenticationCredentials extends AuthenticationCredentials {
  version: typeof CREDENTIAL_VERSION;
}

export type CredentialLoadResult =
  | { status: "empty" }
  | { status: "corrupt" }
  | { status: "ready"; credentials: AuthenticationCredentials };

interface SecureStorageDriver {
  isAvailableAsync(): Promise<boolean>;
  getItemAsync(
    key: string,
    options?: SecureStore.SecureStoreOptions,
  ): Promise<string | null>;
  setItemAsync(
    key: string,
    value: string,
    options?: SecureStore.SecureStoreOptions,
  ): Promise<void>;
  deleteItemAsync(
    key: string,
    options?: SecureStore.SecureStoreOptions,
  ): Promise<void>;
}

interface SecureCredentialStoreOptions {
  apiEnvironment?: ApiEnvironment;
  storage?: SecureStorageDriver;
  createInstallationId?: () => string;
}

export class SecureStorageUnavailableError extends Error {
  constructor() {
    super("Protected credential storage is unavailable.");
    this.name = "SecureStorageUnavailableError";
  }
}

export interface SecureCredentialStore {
  load(): Promise<CredentialLoadResult>;
  save(credentials: AuthenticationCredentials): Promise<void>;
  clearAuthentication(): Promise<void>;
  getOrCreateInstallationId(): Promise<string>;
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.length > 0;
}

function isTimestamp(value: unknown): value is string {
  return isNonEmptyString(value) && Number.isFinite(Date.parse(value));
}

function isStoredCredentials(
  value: unknown,
): value is StoredAuthenticationCredentials {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  const user = candidate.user;
  return (
    candidate.version === CREDENTIAL_VERSION &&
    isNonEmptyString(candidate.accessToken) &&
    isTimestamp(candidate.accessTokenExpiresAt) &&
    isNonEmptyString(candidate.refreshToken) &&
    isNonEmptyString(candidate.sessionId) &&
    isTimestamp(candidate.sessionExpiresAt) &&
    isNonEmptyString(candidate.deviceId) &&
    typeof user === "object" &&
    user !== null &&
    isNonEmptyString((user as Record<string, unknown>).id) &&
    isNonEmptyString((user as Record<string, unknown>).email)
  );
}

function isUuid(value: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
    value,
  );
}

function createCryptographicUuid(): string {
  const id = globalThis.crypto?.randomUUID?.();
  if (!id) {
    throw new SecureStorageUnavailableError();
  }
  return id;
}

export function createSecureCredentialStore({
  apiEnvironment = getRuntimeEnvironment().apiEnvironment,
  storage = SecureStore,
  createInstallationId = createCryptographicUuid,
}: SecureCredentialStoreOptions = {}): SecureCredentialStore {
  const keyPrefix = `achiwave.${apiEnvironment}`;
  const authenticationKey = `${keyPrefix}.authentication`;
  const installationKey = `${keyPrefix}.installation`;

  async function assertAvailable(): Promise<void> {
    if (!(await storage.isAvailableAsync())) {
      throw new SecureStorageUnavailableError();
    }
  }

  return {
    async load(): Promise<CredentialLoadResult> {
      await assertAvailable();
      const serialized = await storage.getItemAsync(
        authenticationKey,
        SECURE_STORE_OPTIONS,
      );
      if (serialized === null) {
        return { status: "empty" };
      }
      try {
        const parsed: unknown = JSON.parse(serialized);
        if (!isStoredCredentials(parsed)) {
          throw new Error("Invalid protected credential envelope.");
        }
        const { version: _version, ...credentials } = parsed;
        return { status: "ready", credentials };
      } catch {
        await storage.deleteItemAsync(authenticationKey, SECURE_STORE_OPTIONS);
        return { status: "corrupt" };
      }
    },

    async save(credentials: AuthenticationCredentials): Promise<void> {
      await assertAvailable();
      const stored: StoredAuthenticationCredentials = {
        version: CREDENTIAL_VERSION,
        ...credentials,
      };
      if (!isStoredCredentials(stored)) {
        throw new Error("Authentication credentials are incomplete.");
      }
      await storage.setItemAsync(
        authenticationKey,
        JSON.stringify(stored),
        SECURE_STORE_OPTIONS,
      );
    },

    async clearAuthentication(): Promise<void> {
      await assertAvailable();
      await storage.deleteItemAsync(authenticationKey, SECURE_STORE_OPTIONS);
    },

    async getOrCreateInstallationId(): Promise<string> {
      await assertAvailable();
      const stored = await storage.getItemAsync(
        installationKey,
        SECURE_STORE_OPTIONS,
      );
      if (stored !== null && isUuid(stored)) {
        return stored;
      }
      const generated = createInstallationId();
      if (!isUuid(generated)) {
        throw new Error("A valid installation identifier could not be created.");
      }
      await storage.setItemAsync(
        installationKey,
        generated,
        SECURE_STORE_OPTIONS,
      );
      return generated;
    },
  };
}

export const secureCredentialStore = createSecureCredentialStore();
