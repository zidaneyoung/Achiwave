export interface CompletionSubmission<Input, Result> {
  input: Input;
  promise: Promise<Result>;
  reused: boolean;
}

interface SubmissionEntry<Input, Result> {
  input: Input;
  promise: Promise<Result> | null;
  state: "in_flight" | "retryable_failure";
}

export class CompletionSubmissionRegistry<Input, Result> {
  private readonly entries = new Map<string, SubmissionEntry<Input, Result>>();

  run(
    key: string,
    createInput: () => Input,
    execute: (input: Input) => Promise<Result>,
  ): CompletionSubmission<Input, Result> {
    const existing = this.entries.get(key);
    if (existing?.state === "in_flight" && existing.promise) {
      return { input: existing.input, promise: existing.promise, reused: true };
    }

    const input = existing?.input ?? createInput();
    const promise = execute(input);
    const entry: SubmissionEntry<Input, Result> = {
      input,
      promise,
      state: "in_flight",
    };
    this.entries.set(key, entry);
    void promise.then(
      () => {
        if (this.entries.get(key) === entry) this.entries.delete(key);
      },
      () => {
        if (this.entries.get(key) === entry) {
          entry.promise = null;
          entry.state = "retryable_failure";
        }
      },
    );
    return { input, promise, reused: existing !== undefined };
  }

  getInput(key: string): Input | null {
    return this.entries.get(key)?.input ?? null;
  }

  isInFlight(key: string): boolean {
    return this.entries.get(key)?.state === "in_flight";
  }

  clear(key: string): void {
    this.entries.delete(key);
  }
}
