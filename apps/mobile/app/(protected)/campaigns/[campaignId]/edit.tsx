import { useCallback, useRef, useState } from "react";
import { AccessibilityInfo, StyleSheet, View } from "react-native";
import { Stack, useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";

import { useAuthentication } from "../../../../src/auth/AuthContext";
import { campaignApi, CampaignRequestError } from "../../../../src/campaigns/api";
import type { Campaign, CampaignDetail } from "../../../../src/campaigns/types";
import { validateCampaignForm } from "../../../../src/campaigns/form";
import { AppButton } from "../../../../src/components/AppButton";
import { ErrorState } from "../../../../src/components/ErrorState";
import { AppTextField } from "../../../../src/components/FormControls";
import { LoadingSkeleton } from "../../../../src/components/LoadingSkeleton";
import { PROTECTED_ROUTES } from "../../../../src/navigation/routes";
import { KeyboardAwareScreen } from "../../../../src/platform/KeyboardAwareScreen";
import { AppText } from "../../../../src/theme/AppText";
import { spacing } from "../../../../src/theme/tokens";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/iu;

interface CampaignEditFormProps {
  campaign: CampaignDetail;
  onSaved: (campaign: Campaign) => void;
}

function CampaignEditForm({ campaign, onSaved }: CampaignEditFormProps) {
  const [title, setTitle] = useState(campaign.title);
  const [description, setDescription] = useState(campaign.description ?? "");
  const [attempted, setAttempted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [staleCurrent, setStaleCurrent] = useState<Campaign | null>(null);
  const submissionIdentity = useRef<{ payloadKey: string; mutationId: string } | null>(null);
  const validation = validateCampaignForm(title, description);

  async function submit() {
    setAttempted(true);
    setSubmissionError(null);
    if (validation.titleError || validation.descriptionError || submitting || staleCurrent) return;
    const payloadKey = JSON.stringify({
      description: validation.description,
      recordVersion: campaign.recordVersion,
      title: validation.title,
    });
    if (submissionIdentity.current?.payloadKey !== payloadKey) {
      submissionIdentity.current = {
        payloadKey,
        mutationId: campaignApi.createMutationId(),
      };
    }
    setSubmitting(true);
    try {
      const updated = await campaignApi.update(campaign.id, {
        title: validation.title,
        description: validation.description,
        recordVersion: campaign.recordVersion,
        clientMutationId: submissionIdentity.current.mutationId,
      });
      AccessibilityInfo.announceForAccessibility("Campaign updated.");
      onSaved(updated);
    } catch (error) {
      const message =
        error instanceof CampaignRequestError
          ? error.message
          : "The campaign could not be updated.";
      if (error instanceof CampaignRequestError && error.currentCampaign) {
        setStaleCurrent(error.currentCampaign);
      }
      setSubmissionError(message);
      AccessibilityInfo.announceForAccessibility(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <AppText accessibilityRole="header" variant="heading1">Edit campaign</AppText>
      <AppText tone="muted">Changes use server version {campaign.recordVersion}.</AppText>
      <View style={styles.fields}>
        <AppTextField
          editable={!submitting && !staleCurrent}
          errorText={attempted ? validation.titleError ?? undefined : undefined}
          label="Title"
          maxLength={121}
          onChangeText={setTitle}
          required
          value={title}
        />
        <AppTextField
          editable={!submitting && !staleCurrent}
          errorText={attempted ? validation.descriptionError ?? undefined : undefined}
          helperText="Optional planning context."
          label="Description"
          maxLength={4_001}
          multiline
          numberOfLines={5}
          onChangeText={setDescription}
          textAlignVertical="top"
          value={description}
        />
      </View>
      {submissionError ? (
        <View style={styles.error}>
          <ErrorState kind="inline" />
          <AppText accessibilityLiveRegion="assertive" tone="error">{submissionError}</AppText>
          {staleCurrent ? (
            <AppText tone="muted">
              Server now has “{staleCurrent.title}” at version {staleCurrent.recordVersion}. Your draft has not overwritten it.
            </AppText>
          ) : null}
        </View>
      ) : null}
      <AppButton
        disabled={staleCurrent !== null}
        label="Save campaign"
        loading={submitting}
        onPress={() => void submit()}
      />
    </>
  );
}

export default function EditCampaignRoute() {
  const parameters = useLocalSearchParams<{ campaignId?: string | string[] }>();
  const rawCampaignId = parameters.campaignId;
  const campaignId = typeof rawCampaignId === "string" && UUID.test(rawCampaignId) ? rawCampaignId : null;
  const authentication = useAuthentication();
  const ownerId = authentication.state.status === "authenticated" ? authentication.state.user.id : null;
  const router = useRouter();
  const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const requestSequence = useRef(0);

  const load = useCallback(async () => {
    if (!campaignId || !ownerId) return;
    const request = ++requestSequence.current;
    setError(null);
    try {
      const result = await campaignApi.get(campaignId);
      if (request === requestSequence.current) setCampaign(result);
    } catch (caught) {
      if (request !== requestSequence.current) return;
      setError(
        caught instanceof CampaignRequestError
          ? caught.message
          : "This campaign could not be loaded.",
      );
    }
  }, [campaignId, ownerId]);

  useFocusEffect(
    useCallback(() => {
      void load();
      return () => {
        requestSequence.current += 1;
      };
    }, [load]),
  );

  if (!ownerId) return null;
  return (
    <KeyboardAwareScreen contentContainerStyle={styles.content}>
      <Stack.Screen options={{ title: "Edit campaign" }} />
      {!campaign && !error && campaignId ? (
        <LoadingSkeleton label="Loading campaign form" layout="card" />
      ) : null}
      {(!campaign && error) || !campaignId ? (
        <View style={styles.error}>
          <ErrorState kind="fullScreen" onRetry={campaignId ? () => void load() : undefined} />
          <AppText accessibilityLiveRegion="assertive" tone="error">
            {campaignId ? error : "This campaign link is invalid."}
          </AppText>
        </View>
      ) : null}
      {campaign ? (
        <CampaignEditForm
          key={`${campaign.id}:${campaign.recordVersion}`}
          campaign={campaign}
          onSaved={(updated) => {
            router.replace(PROTECTED_ROUTES.campaignDetail(updated.id));
          }}
        />
      ) : null}
    </KeyboardAwareScreen>
  );
}

const styles = StyleSheet.create({
  content: {
    flexGrow: 1,
    gap: spacing.sm,
    padding: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  fields: { gap: spacing.md, marginVertical: spacing.sm },
  error: { gap: spacing.xs },
});
