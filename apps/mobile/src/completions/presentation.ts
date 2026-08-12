import type { CompleteOccurrenceInput } from "./api";
import type { CompleteOccurrenceResult } from "./types";
import type { CompletionFailure } from "./failure";
import type { Quest } from "../quests/types";

export interface CompletionCanonicalSnapshot {
  occurrenceId: string;
  occurrenceStatus: Quest["occurrence"] extends infer _Occurrence
    ? "scheduled" | "available" | "completed" | "reversed" | "expired" | "voided"
    : never;
  occurrenceVersion: number;
  activeCompletionId: string | null;
  campaignId: string;
  campaignStatus: Quest["campaignStatus"];
  campaignVersion: number;
  eventSequence: number | null;
}

export type CompletionPresentation =
  | {
      phase: "pending";
      canonical: CompletionCanonicalSnapshot;
      mutationId: string;
      confirmedResult: null;
    }
  | {
      phase: "synchronized";
      canonical: CompletionCanonicalSnapshot;
      mutationId: string;
      confirmedResult: CompleteOccurrenceResult;
    }
  | {
      phase: "retryable_failure" | "permanent_failure";
      canonical: CompletionCanonicalSnapshot;
      mutationId: string;
      confirmedResult: null;
      failure: CompletionFailure;
    };

const records = new Map<string, CompletionPresentation>();
const listeners = new Map<string, Set<() => void>>();

function key(ownerId: string, occurrenceId: string): string {
  return `${ownerId}:${occurrenceId}`;
}

function canonicalFromQuest(quest: Quest): CompletionCanonicalSnapshot | null {
  if (!quest.occurrence) return null;
  return {
    occurrenceId: quest.occurrence.id,
    occurrenceStatus: quest.occurrence.status,
    occurrenceVersion: quest.occurrence.recordVersion,
    activeCompletionId: quest.occurrence.activeCompletionId,
    campaignId: quest.campaignId,
    campaignStatus: quest.campaignStatus,
    campaignVersion: quest.campaignRecordVersion,
    eventSequence: null,
  };
}

function resultEventSequence(result: CompleteOccurrenceResult): number {
  return Math.max(
    result.completion.eventSequence,
    ...result.progressEvents.map((event) => event.eventSequence),
  );
}

function isNotOlder(
  current: CompletionCanonicalSnapshot,
  incoming: CompletionCanonicalSnapshot,
): boolean {
  if (
    incoming.occurrenceVersion < current.occurrenceVersion ||
    incoming.campaignVersion < current.campaignVersion
  ) {
    return false;
  }
  return current.eventSequence === null ||
    incoming.eventSequence === null ||
    incoming.eventSequence >= current.eventSequence;
}

function emit(recordKey: string): void {
  for (const listener of listeners.get(recordKey) ?? []) listener();
}

export function beginCompletionPresentation(
  ownerId: string,
  quest: Quest,
  input: CompleteOccurrenceInput,
): CompletionPresentation | null {
  const canonical = canonicalFromQuest(quest);
  if (!canonical || canonical.occurrenceId !== input.occurrenceId) return null;
  const record: CompletionPresentation = {
    phase: "pending",
    canonical,
    mutationId: input.clientMutationId,
    confirmedResult: null,
  };
  const recordKey = key(ownerId, input.occurrenceId);
  records.set(recordKey, record);
  emit(recordKey);
  return record;
}

export function confirmCompletionPresentation(
  ownerId: string,
  result: CompleteOccurrenceResult,
): CompletionPresentation {
  const recordKey = key(ownerId, result.occurrence.id);
  const existing = records.get(recordKey);
  const canonical: CompletionCanonicalSnapshot = {
    occurrenceId: result.occurrence.id,
    occurrenceStatus: result.occurrence.status,
    occurrenceVersion: result.occurrence.recordVersion,
    activeCompletionId: result.completion.id,
    campaignId: result.campaign.id,
    campaignStatus: result.campaign.status,
    campaignVersion: result.campaign.recordVersion,
    eventSequence: resultEventSequence(result),
  };
  if (existing && !isNotOlder(existing.canonical, canonical)) return existing;
  const record: CompletionPresentation = {
    phase: "synchronized",
    canonical,
    mutationId: existing?.mutationId ?? "server-confirmed",
    confirmedResult: result,
  };
  records.set(recordKey, record);
  emit(recordKey);
  return record;
}

export function refreshCompletionCanonical(
  ownerId: string,
  quest: Quest,
): CompletionPresentation | null {
  const canonical = canonicalFromQuest(quest);
  if (!canonical) return null;
  const recordKey = key(ownerId, canonical.occurrenceId);
  const existing = records.get(recordKey);
  if (!existing) return null;
  if (!isNotOlder(existing.canonical, canonical)) return existing;
  const record = {
    ...existing,
    canonical: {
      ...canonical,
      eventSequence: canonical.eventSequence ?? existing.canonical.eventSequence,
    },
  };
  records.set(recordKey, record);
  emit(recordKey);
  return record;
}

export function failCompletionPresentation(
  ownerId: string,
  occurrenceId: string,
  mutationId: string,
  failure: CompletionFailure,
): { presentation: CompletionPresentation | null; changed: boolean } {
  const recordKey = key(ownerId, occurrenceId);
  const existing = records.get(recordKey);
  if (!existing || existing.mutationId !== mutationId) {
    return { presentation: existing ?? null, changed: false };
  }
  if (
    (existing.phase === "retryable_failure" || existing.phase === "permanent_failure") &&
    existing.failure.reason === failure.reason
  ) {
    return { presentation: existing, changed: false };
  }
  const record: CompletionPresentation = {
    phase: failure.kind,
    canonical: existing.canonical,
    mutationId,
    confirmedResult: null,
    failure,
  };
  records.set(recordKey, record);
  emit(recordKey);
  return { presentation: record, changed: true };
}

export function clearCompletionPresentation(
  ownerId: string,
  occurrenceId: string,
): void {
  const recordKey = key(ownerId, occurrenceId);
  records.delete(recordKey);
  emit(recordKey);
}

export function getCompletionPresentation(
  ownerId: string | null,
  occurrenceId: string | null,
): CompletionPresentation | null {
  if (!ownerId || !occurrenceId) return null;
  return records.get(key(ownerId, occurrenceId)) ?? null;
}

export function subscribeCompletionPresentation(
  ownerId: string | null,
  occurrenceId: string | null,
  listener: () => void,
): () => void {
  if (!ownerId || !occurrenceId) return () => undefined;
  const recordKey = key(ownerId, occurrenceId);
  const recordListeners = listeners.get(recordKey) ?? new Set();
  recordListeners.add(listener);
  listeners.set(recordKey, recordListeners);
  return () => {
    recordListeners.delete(listener);
    if (recordListeners.size === 0) listeners.delete(recordKey);
  };
}

export async function clearCompletionPresentations(): Promise<void> {
  records.clear();
  for (const recordListeners of listeners.values()) {
    for (const listener of recordListeners) listener();
  }
  listeners.clear();
}
