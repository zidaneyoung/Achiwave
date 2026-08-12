import { secureCredentialStore } from "../auth/secureCredentials";
import { clearCachedPreferences } from "../preferences/cache";
import { clearCachedCampaigns } from "../campaigns/cache";
import { clearCompletionPresentations } from "../completions/presentation";

export interface ProtectedLocalStore {
  id: string;
  purge(): Promise<void>;
}

export interface ProtectedDataPurgeResult {
  status: "complete" | "partial";
  clearedStoreIds: string[];
  failedStoreIds: string[];
}

export function createProtectedDataPurger(stores: ProtectedLocalStore[]) {
  return async function purgeProtectedLocalData(): Promise<ProtectedDataPurgeResult> {
    const clearedStoreIds: string[] = [];
    const failedStoreIds: string[] = [];
    for (const store of stores) {
      try {
        await store.purge();
        clearedStoreIds.push(store.id);
      } catch {
        failedStoreIds.push(store.id);
      }
    }
    return {
      status: failedStoreIds.length === 0 ? "complete" : "partial",
      clearedStoreIds,
      failedStoreIds,
    };
  };
}

export const purgeProtectedLocalData = createProtectedDataPurger([
  {
    id: "authentication",
    purge: () => secureCredentialStore.clearAuthentication(),
  },
  {
    id: "presentation_preferences",
    purge: clearCachedPreferences,
  },
  {
    id: "campaigns",
    purge: clearCachedCampaigns,
  },
  {
    id: "completion_presentations",
    purge: clearCompletionPresentations,
  },
]);
