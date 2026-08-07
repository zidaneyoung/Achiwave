export const QUEST_TITLE_MAX_LENGTH = 120;
const MAX_INTEGER = 2_147_483_647;
const UNSUPPORTED_CONTROL_CHARACTER = /[\u0000-\u001F\u007F]/u;

export interface OneTimeQuestValidation {
  title: string;
  rewardXp: number;
  titleError: string | null;
  rewardError: string | null;
}

export function validateOneTimeQuestForm(
  titleInput: string,
  rewardInput: string,
): OneTimeQuestValidation {
  const title = titleInput.trim();
  const rewardXp = Number(rewardInput);
  let titleError: string | null = null;
  let rewardError: string | null = null;
  if (!title) titleError = "Enter a quest title.";
  else if (title.length > QUEST_TITLE_MAX_LENGTH) titleError = `Use ${QUEST_TITLE_MAX_LENGTH} characters or fewer.`;
  else if (UNSUPPORTED_CONTROL_CHARACTER.test(title)) titleError = "Remove unsupported control characters.";
  if (!/^\d+$/u.test(rewardInput) || !Number.isSafeInteger(rewardXp) || rewardXp > MAX_INTEGER) {
    rewardError = "Enter a whole XP value from 0 to 2147483647.";
  }
  return { title, rewardXp, titleError, rewardError };
}
