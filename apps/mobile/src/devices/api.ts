import { authenticationService } from "../auth/service";

export interface DeviceSnapshot {
  id: string;
  label: string;
  appVersion: string | null;
  buildVersion: string | null;
  state: "active" | "revoked" | "removed";
  registeredAt: string;
  lastSeenAt: string | null;
  isCurrent: boolean;
}

export interface SessionSnapshot {
  id: string;
  deviceId: string;
  deviceLabel: string;
  state: "active" | "revoked" | "expired" | "replaced";
  createdAt: string;
  expiresAt: string;
  lastUsedAt: string | null;
  revokedAt: string | null;
  isCurrent: boolean;
}

interface RevocationResult {
  currentSessionRevoked: boolean;
}

export class DeviceManagementError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DeviceManagementError";
  }
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function stringValue(
  source: Record<string, unknown>,
  key: string,
): string | null {
  const value = source[key];
  return typeof value === "string" && value.length > 0 ? value : null;
}

function nullableStringValue(
  source: Record<string, unknown>,
  key: string,
): string | null | undefined {
  const value = source[key];
  if (value === null) {
    return null;
  }
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

async function responseJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function unexpectedResponse(): DeviceManagementError {
  return new DeviceManagementError(
    "Device security information is temporarily unavailable.",
  );
}

function parseDevice(value: unknown): DeviceSnapshot | null {
  if (!isObject(value)) {
    return null;
  }
  const id = stringValue(value, "id");
  const label = stringValue(value, "label");
  const state = stringValue(value, "device_state");
  const registeredAt = stringValue(value, "registered_at");
  const appVersion = nullableStringValue(value, "app_version");
  const buildVersion = nullableStringValue(value, "build_version");
  const lastSeenAt = nullableStringValue(value, "last_seen_at");
  if (
    !id ||
    !label ||
    (state !== "active" && state !== "revoked" && state !== "removed") ||
    !registeredAt ||
    appVersion === undefined ||
    buildVersion === undefined ||
    lastSeenAt === undefined ||
    typeof value.is_current !== "boolean"
  ) {
    return null;
  }
  return {
    id,
    label,
    appVersion,
    buildVersion,
    state,
    registeredAt,
    lastSeenAt,
    isCurrent: value.is_current,
  };
}

function parseSession(value: unknown): SessionSnapshot | null {
  if (!isObject(value)) {
    return null;
  }
  const id = stringValue(value, "id");
  const deviceId = stringValue(value, "device_id");
  const deviceLabel = stringValue(value, "device_label");
  const state = stringValue(value, "session_state");
  const createdAt = stringValue(value, "created_at");
  const expiresAt = stringValue(value, "expires_at");
  const lastUsedAt = nullableStringValue(value, "last_used_at");
  const revokedAt = nullableStringValue(value, "revoked_at");
  if (
    !id ||
    !deviceId ||
    !deviceLabel ||
    (state !== "active" &&
      state !== "revoked" &&
      state !== "expired" &&
      state !== "replaced") ||
    !createdAt ||
    !expiresAt ||
    lastUsedAt === undefined ||
    revokedAt === undefined ||
    typeof value.is_current !== "boolean"
  ) {
    return null;
  }
  return {
    id,
    deviceId,
    deviceLabel,
    state,
    createdAt,
    expiresAt,
    lastUsedAt,
    revokedAt,
    isCurrent: value.is_current,
  };
}

async function revoke(path: string): Promise<RevocationResult> {
  const response = await authenticationService.request(path, { method: "POST" });
  const body = await responseJson(response);
  if (!response.ok || !isObject(body) || typeof body.current_session_revoked !== "boolean") {
    throw unexpectedResponse();
  }
  const result = { currentSessionRevoked: body.current_session_revoked };
  if (result.currentSessionRevoked) {
    await authenticationService.handleCurrentSessionRevoked();
  }
  return result;
}

export const deviceManagementApi = {
  async listDevices(): Promise<DeviceSnapshot[]> {
    const response = await authenticationService.request("/api/v1/devices");
    const body = await responseJson(response);
    if (!response.ok || !isObject(body) || !Array.isArray(body.devices)) {
      throw unexpectedResponse();
    }
    const devices = body.devices.map(parseDevice);
    if (devices.some((device) => device === null)) {
      throw unexpectedResponse();
    }
    return devices as DeviceSnapshot[];
  },

  async listSessions(): Promise<SessionSnapshot[]> {
    const response = await authenticationService.request("/api/v1/sessions");
    const body = await responseJson(response);
    if (!response.ok || !isObject(body) || !Array.isArray(body.sessions)) {
      throw unexpectedResponse();
    }
    const sessions = body.sessions.map(parseSession);
    if (sessions.some((session) => session === null)) {
      throw unexpectedResponse();
    }
    return sessions as SessionSnapshot[];
  },

  revokeDevice(deviceId: string): Promise<RevocationResult> {
    return revoke(`/api/v1/devices/${encodeURIComponent(deviceId)}/revoke`);
  },

  revokeSession(sessionId: string): Promise<RevocationResult> {
    return revoke(`/api/v1/sessions/${encodeURIComponent(sessionId)}/revoke`);
  },
};
