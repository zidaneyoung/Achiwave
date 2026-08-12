import NetInfo from "@react-native-community/netinfo";
import { useEffect } from "react";

import { completionQueue } from "./queue";
import { synchronizeCompletionQueue } from "./sync";

export function useCompletionSynchronization(
  accountId: string | null,
  enabled: boolean,
  onReconnectWhileLimited: (() => Promise<void>) | null,
): void {
  useEffect(() => {
    if (!accountId) return;
    let active = true;
    let wasOffline = false;
    const synchronizeIfOnline = async (
      connected: boolean,
      internetReachable: boolean | null,
    ) => {
      const online = connected && internetReachable !== false;
      if (!online) {
        wasOffline = true;
        return;
      }
      if (onReconnectWhileLimited) {
        await onReconnectWhileLimited();
        return;
      }
      if (!enabled) return;
      await completionQueue.initialize(accountId);
      if (active && (wasOffline || online)) {
        wasOffline = false;
        await synchronizeCompletionQueue(accountId);
      }
    };
    const unsubscribe = NetInfo.addEventListener((state) => {
      if (!active) return;
      void synchronizeIfOnline(
        state.isConnected === true,
        state.isInternetReachable,
      );
    });
    return () => {
      active = false;
      unsubscribe();
    };
  }, [accountId, enabled, onReconnectWhileLimited]);
}
