export type DirtyFormGuardState<TAction> =
  | { phase: "idle"; action: null }
  | { phase: "prompting"; action: TAction }
  | { phase: "dispatching"; action: TAction }
  | { phase: "committing"; action: null };

export type DirtyFormGuardEvent<TAction> =
  | { type: "intercept"; action: TAction }
  | { type: "stay" }
  | { type: "discard" }
  | { type: "commit" }
  | { type: "settled" };

export function createDirtyFormGuardState<TAction>(): DirtyFormGuardState<TAction> {
  return { phase: "idle", action: null };
}

export function reduceDirtyFormGuard<TAction>(
  state: DirtyFormGuardState<TAction>,
  event: DirtyFormGuardEvent<TAction>,
): DirtyFormGuardState<TAction> {
  if (event.type === "commit") return { phase: "committing", action: null };
  if (event.type === "settled") return createDirtyFormGuardState();
  if (event.type === "intercept") {
    return state.phase === "idle"
      ? { phase: "prompting", action: event.action }
      : state;
  }
  if (event.type === "stay") {
    return state.phase === "prompting" ? createDirtyFormGuardState() : state;
  }
  if (event.type === "discard") {
    return state.phase === "prompting"
      ? { phase: "dispatching", action: state.action }
      : state;
  }
  return state;
}

export function shouldPreventDirtyFormRemoval<TAction>(
  dirty: boolean,
  state: DirtyFormGuardState<TAction>,
): boolean {
  return dirty && (state.phase === "idle" || state.phase === "prompting");
}
