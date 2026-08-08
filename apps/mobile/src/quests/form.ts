export const QUEST_TITLE_MAX_LENGTH = 120;
export const QUEST_DESCRIPTION_MAX_LENGTH = 4_000;
const MAX_INTEGER = 2_147_483_647;
const UNSUPPORTED_CONTROL_CHARACTER = /[\u0000-\u001F\u007F]/u;
const UNSUPPORTED_DESCRIPTION_CONTROL = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/u;

export interface OneTimeQuestValidation {
  title: string;
  rewardXp: number;
  description: string | null;
  titleError: string | null;
  rewardError: string | null;
  descriptionError: string | null;
}

export function validateOneTimeQuestForm(
  titleInput: string,
  rewardInput: string,
  descriptionInput = "",
): OneTimeQuestValidation {
  const title = titleInput.trim();
  const rewardXp = Number(rewardInput);
  const description = descriptionInput.trim() || null;
  let titleError: string | null = null;
  let rewardError: string | null = null;
  let descriptionError: string | null = null;
  if (!title) titleError = "Enter a quest title.";
  else if (title.length > QUEST_TITLE_MAX_LENGTH) titleError = `Use ${QUEST_TITLE_MAX_LENGTH} characters or fewer.`;
  else if (UNSUPPORTED_CONTROL_CHARACTER.test(title)) titleError = "Remove unsupported control characters.";
  if (!/^\d+$/u.test(rewardInput) || !Number.isSafeInteger(rewardXp) || rewardXp > MAX_INTEGER) {
    rewardError = "Enter a whole XP value from 0 to 2147483647.";
  }
  if (description !== null && description.length > QUEST_DESCRIPTION_MAX_LENGTH) {
    descriptionError = `Use ${QUEST_DESCRIPTION_MAX_LENGTH} characters or fewer.`;
  } else if (description !== null && UNSUPPORTED_DESCRIPTION_CONTROL.test(description)) {
    descriptionError = "Remove unsupported control characters.";
  }
  return { title, rewardXp, description, titleError, rewardError, descriptionError };
}
