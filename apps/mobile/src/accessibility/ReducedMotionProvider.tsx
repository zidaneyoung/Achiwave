import type { ReactNode } from "react";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { AccessibilityInfo } from "react-native";

import { loadCachedPreferences } from "../preferences/cache";
import type { ReducedMotionPreference } from "../preferences/types";
import {
  resolveReducedMotion,
  subscribeReducedMotionPreference,
} from "./reducedMotion";

const ReducedMotionContext = createContext(false);

export function ReducedMotionProvider({ children }: { children: ReactNode }) {
  const [preference, setPreference] = useState<ReducedMotionPreference>("system");
  const [systemReduceMotion, setSystemReduceMotion] = useState(false);

  useEffect(() => {
    void AccessibilityInfo.isReduceMotionEnabled().then(setSystemReduceMotion);
    const systemSubscription = AccessibilityInfo.addEventListener(
      "reduceMotionChanged",
      setSystemReduceMotion,
    );
    const preferenceSubscription = subscribeReducedMotionPreference(setPreference);
    void loadCachedPreferences().then((cached) => {
      if (cached) setPreference(cached.reducedMotion);
    });
    return () => {
      systemSubscription.remove();
      preferenceSubscription();
    };
  }, []);

  const reduced = useMemo(
    () => resolveReducedMotion(preference, systemReduceMotion),
    [preference, systemReduceMotion],
  );
  return <ReducedMotionContext.Provider value={reduced}>{children}</ReducedMotionContext.Provider>;
}

export function useReducedMotion() {
  return useContext(ReducedMotionContext);
}
