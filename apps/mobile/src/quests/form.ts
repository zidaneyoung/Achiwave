export const QUEST_TITLE_MAX_LENGTH = 120;
export const QUEST_DESCRIPTION_MAX_LENGTH = 4_000;
const DEFAULT_ALLOWED_REWARD_XP = [0, 10, 20] as const;
const UNSUPPORTED_CONTROL_CHARACTER = /[\u0000-\u001F\u007F]/u;
const UNSUPPORTED_DESCRIPTION_CONTROL = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/u;

export interface OneTimeQuestValidation {
  title: string;
  rewardXp: number;
  description: string | null;
  dueLocalDateTime: string | null;
  titleError: string | null;
  rewardError: string | null;
  descriptionError: string | null;
  dueError: string | null;
}

export function validateOneTimeQuestForm(
  titleInput: string,
  rewardInput: string,
  descriptionInput = "",
  dueInput = "",
  allowedRewardXpValues: readonly number[] = DEFAULT_ALLOWED_REWARD_XP,
): OneTimeQuestValidation {
  const title = titleInput.trim();
  const rewardXp = Number(rewardInput);
  const description = descriptionInput.trim() || null;
  const dueLocalDateTime = dueInput.trim() || null;
  let titleError: string | null = null;
  let rewardError: string | null = null;
  let descriptionError: string | null = null;
  let dueError: string | null = null;
  if (!title) titleError = "Enter a quest title.";
  else if (title.length > QUEST_TITLE_MAX_LENGTH) titleError = `Use ${QUEST_TITLE_MAX_LENGTH} characters or fewer.`;
  else if (UNSUPPORTED_CONTROL_CHARACTER.test(title)) titleError = "Remove unsupported control characters.";
  if (
    !/^\d+$/u.test(rewardInput) ||
    !Number.isSafeInteger(rewardXp) ||
    !allowedRewardXpValues.includes(rewardXp)
  ) {
    rewardError = `Choose an allowed XP reward: ${allowedRewardXpValues.join(", ")}.`;
  }
  if (description !== null && description.length > QUEST_DESCRIPTION_MAX_LENGTH) {
    descriptionError = `Use ${QUEST_DESCRIPTION_MAX_LENGTH} characters or fewer.`;
  } else if (description !== null && UNSUPPORTED_DESCRIPTION_CONTROL.test(description)) {
    descriptionError = "Remove unsupported control characters.";
  }
  if (dueLocalDateTime !== null) {
    const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/u.exec(dueLocalDateTime);
    if (!match) {
      dueError = "Use YYYY-MM-DDTHH:MM, for example 2027-03-14T09:30.";
    } else {
      const [, year, month, day, hour, minute] = match;
      const parts = [year, month, day, hour, minute].map(Number);
      const candidate = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2], parts[3], parts[4]));
      if (
        candidate.getUTCFullYear() !== parts[0] ||
        candidate.getUTCMonth() !== parts[1] - 1 ||
        candidate.getUTCDate() !== parts[2] ||
        candidate.getUTCHours() !== parts[3] ||
        candidate.getUTCMinutes() !== parts[4]
      ) {
        dueError = "Enter a valid local date and time.";
      }
    }
  }
  return {
    title,
    rewardXp,
    description,
    dueLocalDateTime,
    titleError,
    rewardError,
    descriptionError,
    dueError,
  };
}
