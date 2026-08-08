import type { QuestCategory, QuestDifficulty } from "../quests/types";

export interface CampaignFormSnapshot {
  title: string;
  description: string | null;
}

export interface QuestFormSnapshot extends CampaignFormSnapshot {
  category: QuestCategory | null;
  difficulty: QuestDifficulty | null;
  reward: string;
  committedDue: string | null;
}

function canonicalOptionalText(value: string | null | undefined): string | null {
  return value?.trim() || null;
}

export function createCampaignFormSnapshot(
  title: string,
  description: string | null | undefined,
): CampaignFormSnapshot {
  return {
    title: title.trim(),
    description: canonicalOptionalText(description),
  };
}

export function campaignFormSnapshotsEqual(
  left: CampaignFormSnapshot,
  right: CampaignFormSnapshot,
): boolean {
  return left.title === right.title && left.description === right.description;
}

export function createQuestFormSnapshot(input: {
  title: string;
  description: string | null | undefined;
  category: QuestCategory | null;
  difficulty: QuestDifficulty | null;
  reward: string;
  committedDue: string | null | undefined;
}): QuestFormSnapshot {
  return {
    ...createCampaignFormSnapshot(input.title, input.description),
    category: input.category,
    difficulty: input.difficulty,
    reward: input.reward.trim(),
    committedDue: canonicalOptionalText(input.committedDue),
  };
}

export function questFormSnapshotsEqual(
  left: QuestFormSnapshot,
  right: QuestFormSnapshot,
): boolean {
  return (
    campaignFormSnapshotsEqual(left, right) &&
    left.category === right.category &&
    left.difficulty === right.difficulty &&
    left.reward === right.reward &&
    left.committedDue === right.committedDue
  );
}
