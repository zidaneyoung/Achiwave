import { useCallback, useEffect, useRef, useState } from "react";
import { Keyboard } from "react-native";
import {
  useNavigation,
  usePreventRemove,
  type NavigationAction,
} from "expo-router/react-navigation";

import { AppDialog } from "../components/Overlays";
import {
  createDirtyFormGuardState,
  reduceDirtyFormGuard,
  shouldPreventDirtyFormRemoval,
  type DirtyFormGuardState,
} from "./dirtyFormGuard";

export interface DirtyFormGuard {
  completeNavigation: (navigate: () => void) => void;
  discardChanges: () => void;
  dialogVisible: boolean;
  stay: () => void;
}

export function useDirtyFormGuard(dirty: boolean): DirtyFormGuard {
  const navigation = useNavigation();
  const [state, setState] = useState<DirtyFormGuardState<NavigationAction>>(
    createDirtyFormGuardState,
  );
  const committedNavigation = useRef<(() => void) | null>(null);
  const dispatchedState = useRef<DirtyFormGuardState<NavigationAction> | null>(null);
  const preventRemove = shouldPreventDirtyFormRemoval(dirty, state);

  usePreventRemove(preventRemove, ({ data }) => {
    Keyboard.dismiss();
    setState((current) =>
      reduceDirtyFormGuard(current, { type: "intercept", action: data.action }),
    );
  });

  useEffect(() => {
    if (state.phase === "dispatching") {
      if (dispatchedState.current === state) return;
      dispatchedState.current = state;
      navigation.dispatch(state.action);
      setState((current) => reduceDirtyFormGuard(current, { type: "settled" }));
      return;
    }
    if (state.phase === "committing") {
      const navigate = committedNavigation.current;
      committedNavigation.current = null;
      navigate?.();
    }
  }, [navigation, state]);

  const completeNavigation = useCallback((navigate: () => void) => {
    if (committedNavigation.current) return;
    committedNavigation.current = navigate;
    setState((current) => reduceDirtyFormGuard(current, { type: "commit" }));
  }, []);

  const stay = useCallback(() => {
    dispatchedState.current = null;
    setState((current) => reduceDirtyFormGuard(current, { type: "stay" }));
  }, []);

  const discardChanges = useCallback(() => {
    setState((current) => reduceDirtyFormGuard(current, { type: "discard" }));
  }, []);

  return {
    completeNavigation,
    discardChanges,
    dialogVisible: state.phase === "prompting",
    stay,
  };
}

export function DirtyFormDialog({
  busy = false,
  guard,
}: {
  busy?: boolean;
  guard: DirtyFormGuard;
}) {
  return (
    <AppDialog
      busy={busy}
      confirmLabel="Discard changes"
      description="Your unsaved changes will be lost."
      dismissLabel="Stay"
      kind="destructive"
      onConfirm={guard.discardChanges}
      onDismiss={guard.stay}
      title="Discard changes?"
      visible={guard.dialogVisible}
    />
  );
}
