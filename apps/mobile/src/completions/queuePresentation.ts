import type { CompletionQueueRecord, CompletionQueueState } from "./queueTypes";

export interface QueueStatePresentation {
  label: string;
  announcement: string;
  tone: "error" | "info" | "neutral" | "success" | "warning";
  action: "dismiss_and_refresh" | "retry" | null;
}

export function completionQueueStatePresentation(
  state: CompletionQueueState,
): QueueStatePresentation {
  switch (state) {
    case "pending":
      return {
        label: "Pending completion — waiting to synchronize",
        announcement: "Completion is pending synchronization.",
        tone: "warning",
        action: null,
      };
    case "in_flight":
      return {
        label: "Synchronizing completion — server confirmation pending",
        announcement: "Completion synchronization started.",
        tone: "info",
        action: null,
      };
    case "succeeded":
      return {
        label: "Completion synchronized — canonical result stored",
        announcement: "Completion synchronized with the server.",
        tone: "success",
        action: null,
      };
    case "retryable_failure":
      return {
        label: "Synchronization paused — retry available",
        announcement: "Completion synchronization paused. Retry is available.",
        tone: "error",
        action: "retry",
      };
    case "permanent_failure":
      return {
        label: "Completion rejected — latest server state wins",
        announcement: "Completion was rejected. Review the latest quest state.",
        tone: "error",
        action: "dismiss_and_refresh",
      };
    case "cancelled":
      return {
        label: "Pending completion cancelled — not submitted",
        announcement: "Pending completion was cancelled.",
        tone: "neutral",
        action: null,
      };
  }
}

export function isCompletionQueueRecordRelevant(
  record: CompletionQueueRecord,
  activeCompletionId: string | null,
): boolean {
  return record.state !== "succeeded" ||
    (record.completionId !== null && record.completionId === activeCompletionId);
}
