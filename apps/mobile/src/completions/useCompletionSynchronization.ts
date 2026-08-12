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
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let scheduleGeneration = 0;
    const scheduleNext = async () => {
      if (!active || !enabled) return;
      const generation = ++scheduleGeneration;
      if (retryTimer !== null) {
        clearTimeout(retryTimer);
        retryTimer = null;
      }
      const dueAt = await completionQueue.nextDueAt(accountId);
      if (!active || generation !== scheduleGeneration || dueAt === null) return;
      const delay = Math.max(5_000, Date.parse(dueAt) - Date.now());
      retryTimer = setTimeout(() => {
        retryTimer = null;
        void synchronizeCompletionQueue(accountId).then(scheduleNext).catch(() => undefined);
      }, delay);
    };
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
        await scheduleNext();
      }
    };
    const unsubscribe = NetInfo.addEventListener((state) => {
      if (!active) return;
      void synchronizeIfOnline(
        state.isConnected === true,
        state.isInternetReachable,
      ).catch(() => undefined);
    });
    const unsubscribeQueue = completionQueue.subscribePartition(accountId, () => {
      void scheduleNext().catch(() => undefined);
    });
    return () => {
      active = false;
      if (retryTimer !== null) clearTimeout(retryTimer);
      unsubscribe();
      unsubscribeQueue();
    };
  }, [accountId, enabled, onReconnectWhileLimited]);
}
