export interface SingleFlightRun<TResult> {
  promise: Promise<TResult>;
  started: boolean;
}

export interface KeyedSingleFlight<TResult> {
  run(key: string, request: () => Promise<TResult>): SingleFlightRun<TResult>;
  has(key: string): boolean;
}

export function createKeyedSingleFlight<TResult>(): KeyedSingleFlight<TResult> {
  const requests = new Map<string, Promise<TResult>>();
  return {
    has(key) {
      return requests.has(key);
    },
    run(key, request) {
      const existing = requests.get(key);
      if (existing) return { promise: existing, started: false };
      const promise = Promise.resolve().then(request);
      requests.set(key, promise);
      void promise.then(
        () => {
          if (requests.get(key) === promise) requests.delete(key);
        },
        () => {
          if (requests.get(key) === promise) requests.delete(key);
        },
      );
      return { promise, started: true };
    },
  };
}
