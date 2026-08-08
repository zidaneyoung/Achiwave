import { useState } from "react";
import { View } from "react-native";

import { AppButton } from "../components/AppButton";
import { AppSelector } from "../components/FormControls";
import { AppBottomSheet } from "../components/Overlays";
import type { QuestAuthoringOption } from "./types";

interface QuestOptionSelectorProps {
  disabled?: boolean;
  errorText?: string;
  helperText?: string;
  label: string;
  nullableLabel?: string;
  onChange: (value: string | null) => void;
  options: QuestAuthoringOption[];
  required?: boolean;
  value: string | null;
}

export function QuestOptionSelector({
  disabled = false,
  errorText,
  helperText,
  label,
  nullableLabel,
  onChange,
  options,
  required = false,
  value,
}: QuestOptionSelectorProps) {
  const [visible, setVisible] = useState(false);
  const selectedLabel = value === null
    ? nullableLabel ?? "Not selected"
    : options.find((option) => option.value === value)?.label ?? "Unavailable choice";
  const choices = nullableLabel
    ? [{ value: null, label: nullableLabel }, ...options]
    : options;

  return (
    <>
      <AppSelector
        disabled={disabled}
        errorText={errorText}
        expanded={visible}
        helperText={helperText}
        label={label}
        onPress={() => setVisible(true)}
        required={required}
        value={selectedLabel}
      />
      <AppBottomSheet
        dismissLabel="Cancel"
        onDismiss={() => setVisible(false)}
        title={`Choose ${label.toLowerCase()}`}
        visible={visible}
      >
        <View>
          {choices.map((option) => {
            const selected = option.value === value;
            return (
              <AppButton
                accessibilityHint={selected ? "Current choice" : `Select ${option.label}`}
                key={option.value ?? "__none__"}
                label={`${option.label}${selected ? " (selected)" : ""}`}
                onPress={() => {
                  onChange(option.value);
                  setVisible(false);
                }}
                variant={selected ? "secondary" : "ghost"}
              />
            );
          })}
        </View>
      </AppBottomSheet>
    </>
  );
}
