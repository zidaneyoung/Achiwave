import { useEffect, useState } from "react";
import { DateTimePickerAndroid } from "@react-native-community/datetimepicker";
import { AccessibilityInfo, Keyboard, Platform, View } from "react-native";

import { AppButton } from "../components/AppButton";
import { AppSelector, AppTextField } from "../components/FormControls";
import {
  commitQuestDueDateTimeSelection,
  formatQuestDueDateTimeValue,
  isSupportedTimeZone,
  pickerValueForLocalDateTime,
} from "./dueDateTime";

interface QuestDueDateTimeFieldProps {
  disabled?: boolean;
  errorText?: string;
  onChange: (value: string) => void;
  timeZoneName: string | null;
  value: string;
}

const PICKER_ERROR = "The date and time picker could not be opened. Try again.";

export function QuestDueDateTimeField({
  disabled = false,
  errorText,
  onChange,
  timeZoneName,
  value,
}: QuestDueDateTimeFieldProps) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerError, setPickerError] = useState<string | null>(null);
  const nativeAndroidPicker = Platform.OS === "android" && isSupportedTimeZone(timeZoneName);
  const helperText = timeZoneName
    ? `Optional local time in ${timeZoneName}. The server validates and resolves it.`
    : "Optional local time. Your saved account timezone is unavailable; the server validates and resolves it.";

  useEffect(() => () => {
    if (Platform.OS !== "android") return;
    void DateTimePickerAndroid.dismiss("date").catch(() => undefined);
    void DateTimePickerAndroid.dismiss("time").catch(() => undefined);
  }, []);

  function reportPickerError() {
    setPickerOpen(false);
    setPickerError(PICKER_ERROR);
    AccessibilityInfo.announceForAccessibility(PICKER_ERROR);
  }

  function openPicker() {
    if (!nativeAndroidPicker || disabled || pickerOpen) return;
    Keyboard.dismiss();
    setPickerError(null);
    setPickerOpen(true);
    const committedValue = value;
    const pickerValue = pickerValueForLocalDateTime(value, timeZoneName, new Date());

    try {
      DateTimePickerAndroid.open({
        display: "default",
        mode: "date",
        negativeButton: { label: "Cancel" },
        onDismiss: () => setPickerOpen(false),
        onError: reportPickerError,
        onValueChange: (_event, selectedDate) => {
          try {
            DateTimePickerAndroid.open({
              display: "default",
              mode: "time",
              negativeButton: { label: "Cancel" },
              onDismiss: () => setPickerOpen(false),
              onError: reportPickerError,
              onValueChange: (_timeEvent, selectedTime) => {
                try {
                  const nextValue = commitQuestDueDateTimeSelection(
                    committedValue,
                    selectedDate,
                    selectedTime,
                    timeZoneName,
                  );
                  onChange(nextValue);
                  setPickerOpen(false);
                  AccessibilityInfo.announceForAccessibility(
                    `Due date and time set to ${formatQuestDueDateTimeValue(nextValue, timeZoneName)}.`,
                  );
                } catch {
                  reportPickerError();
                }
              },
              positiveButton: { label: "Set" },
              timeZoneName,
              value: selectedDate,
            });
          } catch {
            reportPickerError();
          }
        },
        positiveButton: { label: "Next" },
        timeZoneName,
        value: pickerValue,
      });
    } catch {
      reportPickerError();
    }
  }

  if (!nativeAndroidPicker) {
    return (
      <AppTextField
        autoCapitalize="none"
        editable={!disabled}
        errorText={errorText}
        helperText={`${helperText} Use YYYY-MM-DDTHH:MM.`}
        label="Due date and time"
        onChangeText={onChange}
        placeholder="YYYY-MM-DDTHH:MM"
        value={value}
      />
    );
  }

  return (
    <View>
      <AppSelector
        disabled={disabled || pickerOpen}
        errorText={errorText ?? pickerError ?? undefined}
        expanded={pickerOpen}
        helperText={`${helperText} Choose a date, then a time; the value changes only after both are confirmed.`}
        label="Due date and time"
        onPress={openPicker}
        value={value ? formatQuestDueDateTimeValue(value, timeZoneName) : "Not set"}
      />
      {value ? (
        <AppButton
          accessibilityHint="Removes the optional due date and time."
          disabled={disabled || pickerOpen}
          label="Clear due date and time"
          onPress={() => {
            setPickerError(null);
            onChange("");
            AccessibilityInfo.announceForAccessibility("Due date and time cleared.");
          }}
          variant="ghost"
        />
      ) : null}
    </View>
  );
}
