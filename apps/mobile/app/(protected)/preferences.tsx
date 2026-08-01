import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Switch,
  Text,
  View,
} from "react-native";

import { KeyboardAwareScreen } from "../../src/platform/KeyboardAwareScreen";
import { preferenceApi } from "../../src/preferences/api";
import { formatPreferenceDate } from "../../src/preferences/formatDate";
import type {
  DateFormatPreference,
  PreferenceSnapshot,
  ReducedMotionPreference,
} from "../../src/preferences/types";
import {
  type AchiwaveTheme,
  useAchiwaveTheme,
  useThemeStyles,
} from "../../src/theme/ThemeProvider";
import { borders, radii, sizing, spacing, typography } from "../../src/theme/tokens";
import { publishReducedMotionPreference } from "../../src/accessibility/reducedMotion";

const DATE_FORMAT_OPTIONS: Array<{
  value: DateFormatPreference;
  label: string;
}> = [
  { value: "system", label: "Use device setting" },
  { value: "day_month_year", label: "Day / month / year" },
  { value: "month_day_year", label: "Month / day / year" },
  { value: "year_month_day", label: "Year - month - day" },
];

const MOTION_OPTIONS: Array<{
  value: ReducedMotionPreference;
  label: string;
}> = [
  { value: "system", label: "Use device setting" },
  { value: "reduce", label: "Reduce motion" },
  { value: "allow", label: "Allow motion" },
];

const NOTIFICATION_OPTIONS: Array<{
  value: "unspecified" | "enabled" | "disabled";
  label: string;
}> = [
  { value: "unspecified", label: "Not chosen" },
  { value: "enabled", label: "Enabled in Achiwave" },
  { value: "disabled", label: "Disabled in Achiwave" },
];

export default function PreferencesRoute() {
  const theme = useAchiwaveTheme();
  const styles = useThemeStyles(createStyles);
  const [preferences, setPreferences] = useState<PreferenceSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setMessage(null);
    try {
      setPreferences(await preferenceApi.get());
    } catch {
      try {
        const cached = await preferenceApi.getCached();
        setPreferences(cached);
        setMessage(
          cached
            ? "Showing saved preferences. Reconnect before making changes."
            : "Preferences could not be loaded. Check your connection.",
        );
      } catch {
        setMessage("Preferences could not be loaded. Check your connection.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function selectDateFormat(value: DateFormatPreference): Promise<void> {
    if (!preferences || saving || preferences.dateFormat === value) {
      return;
    }
    setSaving(true);
    setMessage(null);
    try {
      setPreferences(
        await preferenceApi.updateDateFormat(value, preferences.recordVersion),
      );
      setMessage("Date format saved.");
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Date format could not be saved.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function updateFeedback(
    updates: { soundEnabled?: boolean; hapticsEnabled?: boolean },
  ): Promise<void> {
    if (!preferences || saving) {
      return;
    }
    setSaving(true);
    setMessage(null);
    try {
      setPreferences(
        await preferenceApi.updateFeedback(updates, preferences.recordVersion),
      );
      setMessage("Feedback preferences saved.");
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Feedback preferences could not be saved.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function selectReducedMotion(
    value: ReducedMotionPreference,
  ): Promise<void> {
    if (!preferences || saving || preferences.reducedMotion === value) {
      return;
    }
    setSaving(true);
    setMessage(null);
    try {
      const updated = await preferenceApi.updateReducedMotion(value, preferences.recordVersion);
      setPreferences(updated);
      publishReducedMotionPreference(updated.reducedMotion);
      setMessage("Motion preference saved.");
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Motion preference could not be saved.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function selectNotification(
    value: "unspecified" | "enabled" | "disabled",
  ): Promise<void> {
    if (
      !preferences ||
      saving ||
      preferences.notificationPreference === value
    ) {
      return;
    }
    setSaving(true);
    setMessage(null);
    try {
      setPreferences(
        await preferenceApi.updateNotification(value, preferences.recordVersion),
      );
      setMessage("Notification preference saved.");
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Notification preference could not be saved.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <KeyboardAwareScreen contentContainerStyle={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          Preferences
        </Text>
        <Text style={styles.introduction}>
          These settings change presentation only. Server timestamps stay unchanged.
        </Text>
        {message ? (
          <Text accessibilityLiveRegion="polite" style={styles.message}>
            {message}
          </Text>
        ) : null}
        {loading ? (
          <ActivityIndicator
            accessibilityLabel="Loading preferences"
            color={theme.colors.accent}
            size="large"
            style={styles.loading}
          />
        ) : preferences ? (
          <View>
            <Text accessibilityRole="header" style={styles.sectionTitle}>
              Date format
            </Text>
            <Text style={styles.preview}>
              Preview: {formatPreferenceDate(new Date(), preferences.dateFormat)}
            </Text>
            {DATE_FORMAT_OPTIONS.map((option) => {
              const selected = option.value === preferences.dateFormat;
              return (
                <Pressable
                  key={option.value}
                  accessibilityRole="radio"
                  accessibilityState={{ selected, disabled: saving }}
                  disabled={saving}
                  onPress={() => void selectDateFormat(option.value)}
                  style={({ pressed }) => [
                    styles.option,
                    selected && styles.optionSelected,
                    pressed && styles.optionPressed,
                  ]}
                >
                  <Text style={styles.optionText}>{option.label}</Text>
                  <Text style={styles.optionState}>{selected ? "Selected" : ""}</Text>
                </Pressable>
              );
            })}
            <Text accessibilityRole="header" style={styles.sectionTitle}>
              Feedback
            </Text>
            <View style={styles.switchRow}>
              <View style={styles.switchCopy}>
                <Text style={styles.optionText}>Sound</Text>
                <Text style={styles.help}>Allow future in-app sound feedback.</Text>
              </View>
              <Switch
                accessibilityLabel="Sound feedback"
                disabled={saving}
                onValueChange={(value) =>
                  void updateFeedback({ soundEnabled: value })
                }
                value={preferences.soundEnabled}
              />
            </View>
            <View style={styles.switchRow}>
              <View style={styles.switchCopy}>
                <Text style={styles.optionText}>Haptics</Text>
                <Text style={styles.help}>Allow future vibration feedback.</Text>
              </View>
              <Switch
                accessibilityLabel="Haptic feedback"
                disabled={saving}
                onValueChange={(value) =>
                  void updateFeedback({ hapticsEnabled: value })
                }
                value={preferences.hapticsEnabled}
              />
            </View>
            <Text accessibilityRole="header" style={styles.sectionTitle}>
              Motion
            </Text>
            {MOTION_OPTIONS.map((option) => {
              const selected = option.value === preferences.reducedMotion;
              return (
                <Pressable
                  key={option.value}
                  accessibilityRole="radio"
                  accessibilityState={{ selected, disabled: saving }}
                  disabled={saving}
                  onPress={() => void selectReducedMotion(option.value)}
                  style={({ pressed }) => [
                    styles.option,
                    selected && styles.optionSelected,
                    pressed && styles.optionPressed,
                  ]}
                >
                  <Text style={styles.optionText}>{option.label}</Text>
                  <Text style={styles.optionState}>{selected ? "Selected" : ""}</Text>
                </Pressable>
              );
            })}
            <Text accessibilityRole="header" style={styles.sectionTitle}>
              Notifications
            </Text>
            <Text style={styles.help}>
              This is your Achiwave preference, not Android permission status.
            </Text>
            {NOTIFICATION_OPTIONS.map((option) => {
              const selected =
                option.value === preferences.notificationPreference;
              return (
                <Pressable
                  key={option.value}
                  accessibilityRole="radio"
                  accessibilityState={{ selected, disabled: saving }}
                  disabled={saving}
                  onPress={() => void selectNotification(option.value)}
                  style={({ pressed }) => [
                    styles.option,
                    selected && styles.optionSelected,
                    pressed && styles.optionPressed,
                  ]}
                >
                  <Text style={styles.optionText}>{option.label}</Text>
                  <Text style={styles.optionState}>{selected ? "Selected" : ""}</Text>
                </Pressable>
              );
            })}
          </View>
        ) : (
          <Pressable
            accessibilityRole="button"
            onPress={() => void load()}
            style={styles.retryButton}
          >
            <Text style={styles.retryButtonText}>Try again</Text>
          </Pressable>
        )}
    </KeyboardAwareScreen>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  container: { padding: spacing.lg, paddingBottom: spacing.xxxl },
  title: { color: theme.colors.foreground, ...typography.heading1 },
  introduction: { color: theme.colors.foregroundMuted, ...typography.body, marginTop: spacing.sm },
  message: { color: theme.colors.warning, ...typography.body, marginTop: spacing.md },
  loading: { marginTop: spacing.xl },
  sectionTitle: { color: theme.colors.foreground, ...typography.heading2, marginTop: spacing.xl },
  preview: { color: theme.colors.foregroundSubtle, ...typography.body, marginTop: spacing.sm },
  option: {
    alignItems: "center",
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderRadius: radii.md,
    borderWidth: borders.thin,
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: spacing.sm,
    minHeight: sizing.formControl,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  optionSelected: { borderColor: theme.colors.borderStrong, borderWidth: borders.selected },
  optionPressed: { backgroundColor: theme.colors.surfacePressed },
  optionText: { color: theme.colors.foreground, flex: 1, ...typography.body },
  optionState: { color: theme.colors.action, ...typography.label, marginLeft: spacing.sm },
  switchRow: {
    alignItems: "center",
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderRadius: radii.md,
    borderWidth: borders.thin,
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: spacing.sm,
    minHeight: sizing.formControl,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  switchCopy: { flex: 1, paddingRight: spacing.md },
  help: { color: theme.colors.foregroundSubtle, ...typography.label, fontWeight: "400", marginTop: spacing.xxs },
  retryButton: {
    alignItems: "center",
    backgroundColor: theme.colors.action,
    borderRadius: radii.md,
    justifyContent: "center",
    marginTop: spacing.lg,
    minHeight: sizing.minimumTouchTarget,
    paddingHorizontal: spacing.md,
  },
  retryButtonText: { color: theme.colors.onAction, ...typography.label },
});
