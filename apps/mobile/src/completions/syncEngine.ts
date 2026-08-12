export interface SynchronizationOperation {
  queueId: string;
}

export type SynchronizationFailure =
  | { kind: "authentication" }
  | {
      kind: "retryable";
      safeClass: string;
      safeMessage: string;
      retryAfterMilliseconds: number | null;
    }
  | {
      kind: "permanent";
      safeClass: string;
      safeMessage: string;
      canonicalResultJson: string | null;
    };

export interface SynchronizationEngineDependencies<
  Operation extends SynchronizationOperation,
  Result,
> {
  validateSession(accountId: string): Promise<void>;
  leaseDue(accountId: string): Promise<Operation[]>;
  submit(operation: Operation): Promise<Result>;
  persistSuccess(operation: Operation, result: Result): Promise<void>;
  afterPersistedSuccess(operation: Operation, result: Result): Promise<void>;
  classifyFailure(error: unknown): SynchronizationFailure;
  persistRetryableFailure(
    operation: Operation,
    failure: Extract<SynchronizationFailure, { kind: "retryable" }>,
  ): Promise<void>;
  persistPermanentFailure(
    operation: Operation,
    failure: Extract<SynchronizationFailure, { kind: "permanent" }>,
  ): Promise<void>;
  releaseLeases(accountId: string, operations: Operation[]): Promise<void>;
}

export interface SynchronizationSummary {
  authenticationPaused: boolean;
  attempted: number;
  succeeded: number;
  retryableFailures: number;
  permanentFailures: number;
}

export function createSynchronizationEngine<
  Operation extends SynchronizationOperation,
  Result,
>(dependencies: SynchronizationEngineDependencies<Operation, Result>) {
  const activeRuns = new Map<string, Promise<SynchronizationSummary>>();

  async function execute(accountId: string): Promise<SynchronizationSummary> {
    const summary: SynchronizationSummary = {
      authenticationPaused: false,
      attempted: 0,
      succeeded: 0,
      retryableFailures: 0,
      permanentFailures: 0,
    };
    try {
      await dependencies.validateSession(accountId);
    } catch (error) {
      if (dependencies.classifyFailure(error).kind === "authentication") {
        summary.authenticationPaused = true;
      }
      return summary;
    }
    const operations = await dependencies.leaseDue(accountId);
    for (let index = 0; index < operations.length; index += 1) {
      const operation = operations[index];
      if (!operation) continue;
      summary.attempted += 1;
      try {
        const result = await dependencies.submit(operation);
        await dependencies.persistSuccess(operation, result);
        summary.succeeded += 1;
        try {
          await dependencies.afterPersistedSuccess(operation, result);
        } catch {
          // Presentation refresh cannot downgrade a durably persisted success.
        }
      } catch (error) {
        const failure = dependencies.classifyFailure(error);
        if (failure.kind === "authentication") {
          summary.authenticationPaused = true;
          await dependencies.releaseLeases(accountId, operations.slice(index));
          break;
        }
        if (failure.kind === "permanent") {
          await dependencies.persistPermanentFailure(operation, failure);
          summary.permanentFailures += 1;
        } else {
          await dependencies.persistRetryableFailure(operation, failure);
          summary.retryableFailures += 1;
        }
      }
    }
    return summary;
  }

  return {
    run(accountId: string): Promise<SynchronizationSummary> {
      const existing = activeRuns.get(accountId);
      if (existing) return existing;
      const run = execute(accountId).finally(() => {
        if (activeRuns.get(accountId) === run) activeRuns.delete(accountId);
      });
      activeRuns.set(accountId, run);
      return run;
    },
  };
}
