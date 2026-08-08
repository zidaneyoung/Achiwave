export interface ArchiveConfirmationCopy {
  title: string;
  description: string;
}

export function campaignArchiveConfirmation(title: string): ArchiveConfirmationCopy {
  return {
    title: `Archive "${title}"?`,
    description:
      "This campaign will be hidden from current views. New quests, recurrence generation, and quest completion will be blocked while it is archived. Existing quests, occurrences, completions, rewards, reversals, and audit history will be preserved. You can restore the campaign later.",
  };
}

export function questArchiveConfirmation(title: string): ArchiveConfirmationCopy {
  return {
    title: `Archive "${title}"?`,
    description:
      "This quest will be hidden from current views. New occurrences and quest completion will be blocked while it is archived. Existing occurrences, completions, rewards, reversals, and audit history will be preserved. You can restore the quest later.",
  };
}
