import type { ReactNode } from "react";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { AccessibilityInfo } from "react-native";

import { loadCachedPreferences } from "../preferences/cache";
import type { ReducedMotionPreference } from "../preferences/types";
import { useAuthentication } from "../auth/AuthContext";
import {
  resolveReducedMotion,
  subscribeReducedMotionPreference,
} from "./reducedMotion";

const ReducedMotionContext = createContext(false);

export function ReducedMotionProvider({ children }: { children: ReactNode }) {
  const { state } = useAuthentication();
  const [preference, setPreference] = useState<ReducedMotionPreference>("system");
  const [systemReduceMotion, setSystemReduceMotion] = useState(false);

  useEffect(() => {
    void AccessibilityInfo.isReduceMotionEnabled().then(setSystemReduceMotion);
    const systemSubscription = AccessibilityInfo.addEventListener(
      "reduceMotionChanged",
      setSystemReduceMotion,
    );
    const preferenceSubscription = subscribeReducedMotionPreference(setPreference);
    return () => {
      systemSubscription.remove();
      preferenceSubscription();
    };
  }, []);

  const ownerId =
    state.status === "authenticated" || state.status === "offline_limited"
      ? state.user.id
      : null;
  useEffect(() => {
    if (!ownerId) {
      setPreference("system");
      return;
    }
    void loadCachedPreferences().then((cached) => {
      setPreference(cached?.reducedMotion ?? "system");
    });
  }, [ownerId]);

  const reduced = useMemo(
    () => resolveReducedMotion(preference, systemReduceMotion),
    [preference, systemReduceMotion],
  );
  return <ReducedMotionContext.Provider value={reduced}>{children}</ReducedMotionContext.Provider>;
}

export function useReducedMotion() {
  return useContext(ReducedMotionContext);
}
