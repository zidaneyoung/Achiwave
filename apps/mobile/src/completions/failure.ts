import type { CompletionRequestError } from "./errors";

export type CompletionFailureReason =
  | "archived"
  | "authentication"
  | "expired"
  | "malformed_mutation"
  | "network"
  | "server"
  | "stale_version"
  | "target_unavailable"
  | "unsupported_schema";

export function unsupportedQueueSchemaFailure(): CompletionFailure {
  return {
    reason: "unsupported_schema",
    kind: "permanent_failure",
    message: "This saved completion was created by an unsupported app version.",
    nextAction: "Refresh and dismiss",
    refreshCanonical: true,
  };
}

export interface CompletionFailure {
  reason: CompletionFailureReason;
  kind: "permanent_failure" | "retryable_failure";
  message: string;
  nextAction: string;
  refreshCanonical: boolean;
}

function stringAt(
  source: unknown,
  section: string,
  field: string,
): string | null {
  if (typeof source !== "object" || source === null) return null;
  const value = (source as Record<string, unknown>)[section];
  return typeof value === "object" && value !== null &&
    typeof (value as Record<string, unknown>)[field] === "string"
    ? (value as Record<string, string>)[field]
    : null;
}

export function classifyCompletionFailure(error: unknown): CompletionFailure {
  if (
    !(error instanceof Error) ||
    error.name !== "CompletionRequestError" ||
    !("code" in error)
  ) {
    return {
      reason: "server",
      kind: "retryable_failure",
      message: "The service could not confirm this completion.",
      nextAction: "Try again",
      refreshCanonical: false,
    };
  }
  const requestError = error as CompletionRequestError;
  if (requestError.code === "authentication") {
    return {
      reason: "authentication",
      kind: "permanent_failure",
      message: "Your session ended before this completion was confirmed.",
      nextAction: "Sign in again",
      refreshCanonical: false,
    };
  }
  if (requestError.code === "offline") {
    return {
      reason: "network",
      kind: "retryable_failure",
      message: "This completion is still unconfirmed because the network is unavailable.",
      nextAction: "Reconnect and retry",
      refreshCanonical: false,
    };
  }
  if (requestError.code === "server" || requestError.code === "invalid_response") {
    return {
      reason: "server",
      kind: "retryable_failure",
      message: "The service could not confirm this completion.",
      nextAction: "Try again",
      refreshCanonical: false,
    };
  }
  if (requestError.code === "not_found") {
    return {
      reason: "target_unavailable",
      kind: "permanent_failure",
      message: "This occurrence is unavailable for this account.",
      nextAction: "Return to quests",
      refreshCanonical: true,
    };
  }
  if (requestError.code === "validation" || requestError.serverCode === "client_mutation_conflict") {
    return {
      reason: "malformed_mutation",
      kind: "permanent_failure",
      message: "This completion request cannot be retried safely.",
      nextAction: "Refresh and try a new action",
      refreshCanonical: true,
    };
  }
  if (requestError.serverCode === "stale_occurrence_version") {
    return {
      reason: "stale_version",
      kind: "permanent_failure",
      message: "This occurrence changed on another device.",
      nextAction: "Review the latest state",
      refreshCanonical: true,
    };
  }
  const occurrenceStatus = stringAt(requestError.current, "occurrence", "status");
  const campaignStatus = stringAt(requestError.current, "campaign", "status");
  if (occurrenceStatus === "expired") {
    return {
      reason: "expired",
      kind: "permanent_failure",
      message: "This occurrence expired before the server accepted completion.",
      nextAction: "Review the current quest",
      refreshCanonical: true,
    };
  }
  if (campaignStatus === "archived") {
    return {
      reason: "archived",
      kind: "permanent_failure",
      message: "This campaign was archived before the server accepted completion.",
      nextAction: "Review the archived campaign",
      refreshCanonical: true,
    };
  }
  return {
    reason: "target_unavailable",
    kind: "permanent_failure",
    message: "This occurrence is no longer eligible for completion.",
    nextAction: "Review the latest state",
    refreshCanonical: true,
  };
}
