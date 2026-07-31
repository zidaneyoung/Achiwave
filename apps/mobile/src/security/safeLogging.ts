const REDACTED = "[REDACTED]";
const SENSITIVE_KEY_PARTS = [
  "access_token",
  "authorization",
  "cookie",
  "credential_digest",
  "database_url",
  "installation_id",
  "password",
  "private_key",
  "redis_url",
  "refresh_token",
  "request_body",
  "secure_store",
  "securestore",
  "secret",
  "signing_key",
  "token_hash",
  "token_value",
] as const;

interface ConsoleSink {
  debug(...data: unknown[]): void;
  error(...data: unknown[]): void;
  info(...data: unknown[]): void;
  warn(...data: unknown[]): void;
}

function normalizedKey(key: string): string {
  return key.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

function isSensitiveKey(key: string): boolean {
  const normalized = normalizedKey(key);
  return (
    normalized === "token" ||
    SENSITIVE_KEY_PARTS.some((part) => normalized.includes(part))
  );
}

function redactText(value: string, redactOpaque = true): string {
  const redacted = value
    .replace(
      /\b([a-z][a-z0-9+.-]*:\/\/)([^@/\s]+)@/gi,
      `$1${REDACTED}@`,
    )
    .replace(/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, `Bearer ${REDACTED}`)
    .replace(
      /(^|[^A-Za-z0-9_-])[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}(?![A-Za-z0-9_-])/g,
      `$1${REDACTED}`,
    )
    .replace(
      /\b(authorization|cookie|password(?:_hash)?|secret|token|access_token|refresh_token|credential_digest|installation_id|database_url|redis_url|signing_key)\b(["']?\s*[:=]\s*["']?)([^"'\s,;&}]+)/gi,
      `$1$2${REDACTED}`,
    );
  return redactOpaque
    ? redacted.replace(
      /(^|[^A-Za-z0-9_-])[A-Za-z0-9_-]{43,}(?![A-Za-z0-9_-])/g,
      `$1${REDACTED}`,
    )
    : redacted;
}

export function sanitizeLogValue(
  value: unknown,
  seen: WeakSet<object> = new WeakSet<object>(),
): unknown {
  if (typeof value === "string") {
    return redactText(value);
  }
  if (
    value === null ||
    typeof value === "undefined" ||
    typeof value === "boolean" ||
    typeof value === "number"
  ) {
    return value;
  }
  if (value instanceof Error) {
    return { exceptionType: value.name };
  }
  if (typeof value !== "object") {
    return `<${typeof value}>`;
  }
  if (seen.has(value)) {
    return "[CIRCULAR]";
  }
  seen.add(value);
  if (Array.isArray(value)) {
    return value.map((item) => sanitizeLogValue(item, seen));
  }
  const sanitized: Record<string, unknown> = {};
  for (const [key, nestedValue] of Object.entries(value)) {
    if (isSensitiveKey(key)) {
      sanitized[key] = REDACTED;
    } else if (
      normalizedKey(key) === "correlationid" &&
      typeof nestedValue === "string"
    ) {
      sanitized[key] = redactText(nestedValue, false);
    } else {
      sanitized[key] = sanitizeLogValue(nestedValue, seen);
    }
  }
  return sanitized;
}

export function createSafeConsole(sink: ConsoleSink = console) {
  function write(
    level: keyof ConsoleSink,
    event: string,
    context?: unknown,
  ): void {
    const safeEvent = redactText(event);
    if (typeof context === "undefined") {
      sink[level](safeEvent);
      return;
    }
    sink[level](safeEvent, sanitizeLogValue(context));
  }

  return {
    debug: (event: string, context?: unknown) => write("debug", event, context),
    error: (event: string, context?: unknown) => write("error", event, context),
    info: (event: string, context?: unknown) => write("info", event, context),
    warn: (event: string, context?: unknown) => write("warn", event, context),
  };
}

export const safeConsole = createSafeConsole();
