import type { CampaignDetail } from "../campaigns/types";
import type { QuestOrder } from "./types";

export type QuestMoveDirection = "up" | "down";

export function moveQuest<T>(
  quests: readonly T[],
  index: number,
  direction: QuestMoveDirection,
): T[] | null {
  const target = direction === "up" ? index - 1 : index + 1;
  if (index < 0 || index >= quests.length || target < 0 || target >= quests.length) {
    return null;
  }
  const result = [...quests];
  [result[index], result[target]] = [result[target], result[index]];
  return result;
}

export function applyQuestOrder(
  detail: CampaignDetail,
  order: QuestOrder,
): CampaignDetail {
  if (detail.id !== order.campaignId) return detail;
  const positions = new Map(order.items.map((item) => [item.id, item]));
  const active = detail.quests
    .filter((quest) => quest.definitionState === "active")
    .map((quest) => {
      const item = positions.get(quest.id);
      return item
        ? { ...quest, displayOrder: item.displayOrder, recordVersion: item.recordVersion }
        : quest;
    })
    .sort((left, right) => left.displayOrder - right.displayOrder || left.id.localeCompare(right.id));
  const archived = detail.quests.filter((quest) => quest.definitionState === "archived");
  return {
    ...detail,
    recordVersion: order.campaignRecordVersion,
    quests: [...active, ...archived],
  };
}
