import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { preferenceApi } from "../../src/preferences/api";
import { formatPreferenceDate } from "../../src/preferences/formatDate";
import type {
  DateFormatPreference,
  PreferenceSnapshot,
  ReducedMotionPreference,
} from "../../src/preferences/types";

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
      setPreferences(
        await preferenceApi.updateReducedMotion(value, preferences.recordVersion),
      );
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
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
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
            color="#1d5b44"
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
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#f7f5ef" },
  container: { padding: 24, paddingBottom: 48 },
  title: { color: "#17221d", fontSize: 30, fontWeight: "700" },
  introduction: { color: "#35423b", fontSize: 17, lineHeight: 24, marginTop: 10 },
  message: { color: "#6d301f", fontSize: 16, lineHeight: 22, marginTop: 16 },
  loading: { marginTop: 32 },
  sectionTitle: { color: "#17221d", fontSize: 23, fontWeight: "700", marginTop: 28 },
  preview: { color: "#46534c", fontSize: 17, marginTop: 10 },
  option: {
    alignItems: "center",
    backgroundColor: "#ffffff",
    borderColor: "#66746c",
    borderRadius: 10,
    borderWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 12,
    minHeight: 52,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  optionSelected: { borderColor: "#1d5b44", borderWidth: 2 },
  optionPressed: { backgroundColor: "#e1ebe5" },
  optionText: { color: "#17221d", flex: 1, fontSize: 17 },
  optionState: { color: "#1d5b44", fontSize: 15, fontWeight: "700", marginLeft: 12 },
  switchRow: {
    alignItems: "center",
    backgroundColor: "#ffffff",
    borderColor: "#c8cec9",
    borderRadius: 10,
    borderWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 12,
    minHeight: 64,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  switchCopy: { flex: 1, paddingRight: 16 },
  help: { color: "#46534c", fontSize: 15, lineHeight: 20, marginTop: 4 },
  retryButton: {
    alignItems: "center",
    backgroundColor: "#1d5b44",
    borderRadius: 10,
    justifyContent: "center",
    marginTop: 24,
    minHeight: 48,
    paddingHorizontal: 18,
  },
  retryButtonText: { color: "#ffffff", fontSize: 17, fontWeight: "700" },
});
