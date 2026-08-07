export const CAMPAIGN_TITLE_MAX_LENGTH = 120;
export const CAMPAIGN_DESCRIPTION_MAX_LENGTH = 4_000;

export interface CampaignFormValidation {
  title: string;
  description: string | null;
  titleError: string | null;
  descriptionError: string | null;
}

const UNSUPPORTED_CONTROL_CHARACTER = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/u;

export function validateCampaignForm(
  titleInput: string,
  descriptionInput: string,
): CampaignFormValidation {
  const title = titleInput.trim();
  const description = descriptionInput.trim() || null;
  let titleError: string | null = null;
  let descriptionError: string | null = null;
  if (!title) {
    titleError = "Enter a campaign title.";
  } else if (title.length > CAMPAIGN_TITLE_MAX_LENGTH) {
    titleError = `Use ${CAMPAIGN_TITLE_MAX_LENGTH} characters or fewer.`;
  } else if (UNSUPPORTED_CONTROL_CHARACTER.test(title)) {
    titleError = "Remove unsupported control characters.";
  }
  if (
    description !== null &&
    description.length > CAMPAIGN_DESCRIPTION_MAX_LENGTH
  ) {
    descriptionError = `Use ${CAMPAIGN_DESCRIPTION_MAX_LENGTH} characters or fewer.`;
  } else if (
    description !== null &&
    UNSUPPORTED_CONTROL_CHARACTER.test(description)
  ) {
    descriptionError = "Remove unsupported control characters.";
  }
  return { title, description, titleError, descriptionError };
}
