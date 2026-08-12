import { useEffect, useState } from "react";

import { completionQueue } from "./queue";
import type { CompletionQueueRecord } from "./queueTypes";

export function useCompletionQueueRecord(
  accountId: string | null,
  occurrenceId: string | null,
): CompletionQueueRecord | null {
  const [record, setRecord] = useState<CompletionQueueRecord | null>(null);
  useEffect(() => {
    let active = true;
    if (!accountId || !occurrenceId) {
      setRecord(null);
      return;
    }
    const load = () => {
      void completionQueue.latest(accountId, occurrenceId).then((next) => {
        if (active) setRecord(next);
      }).catch(() => {
        if (active) setRecord(null);
      });
    };
    load();
    const unsubscribe = completionQueue.subscribe(accountId, occurrenceId, load);
    return () => {
      active = false;
      unsubscribe();
    };
  }, [accountId, occurrenceId]);
  return record;
}
