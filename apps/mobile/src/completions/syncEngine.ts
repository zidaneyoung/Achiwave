export interface SynchronizationOperation {
  queueId: string;
}

export type SynchronizationFailure =
  | { kind: "authentication" }
  | { kind: "retryable"; safeClass: string; safeMessage: string };

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
  releaseLeases(accountId: string, operations: Operation[]): Promise<void>;
}

export interface SynchronizationSummary {
  authenticationPaused: boolean;
  attempted: number;
  succeeded: number;
  retryableFailures: number;
}

export function createSynchronizationEngine<
  Operation extends SynchronizationOperation,
  Result,
>(dependencies: SynchronizationEngineDependencies<Operation, Result>) {
  let activeRun: Promise<SynchronizationSummary> | null = null;

  async function execute(accountId: string): Promise<SynchronizationSummary> {
    const summary: SynchronizationSummary = {
      authenticationPaused: false,
      attempted: 0,
      succeeded: 0,
      retryableFailures: 0,
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
        await dependencies.afterPersistedSuccess(operation, result);
      } catch (error) {
        const failure = dependencies.classifyFailure(error);
        if (failure.kind === "authentication") {
          summary.authenticationPaused = true;
          await dependencies.releaseLeases(accountId, operations.slice(index));
          break;
        }
        await dependencies.persistRetryableFailure(operation, failure);
        summary.retryableFailures += 1;
      }
    }
    return summary;
  }

  return {
    run(accountId: string): Promise<SynchronizationSummary> {
      if (activeRun !== null) return activeRun;
      activeRun = execute(accountId).finally(() => {
        activeRun = null;
      });
      return activeRun;
    },
  };
}
