import { useState } from "react";
import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import {
  Pressable,
  StyleSheet,
  TextInput,
  View,
  type TextInputProps,
} from "react-native";

import { AppText } from "../theme/AppText";
import {
  type AchiwaveTheme,
  useAchiwaveTheme,
  useThemeStyles,
} from "../theme/ThemeProvider";
import { borders, radii, sizing, spacing, typography } from "../theme/tokens";
import { createAndroidRipple } from "../platform/touchFeedback";

interface FieldCopyProps {
  label: string;
  required?: boolean;
  helperText?: string;
  errorText?: string;
}

export interface AppTextFieldProps
  extends Omit<TextInputProps, "accessibilityLabel" | "style">,
    FieldCopyProps {}

export function AppTextField({
  editable = true,
  errorText,
  helperText,
  label,
  onBlur,
  onFocus,
  required = false,
  ...inputProps
}: AppTextFieldProps) {
  const theme = useAchiwaveTheme();
  const styles = useThemeStyles(createStyles);
  const [focused, setFocused] = useState(false);
  const description = errorText ?? helperText;
  return (
    <View style={styles.field}>
      <AppText variant="label">
        {label}{required ? " (required)" : ""}
      </AppText>
      <TextInput
        {...inputProps}
        accessibilityHint={description}
        accessibilityLabel={`${label}${required ? ", required" : ""}`}
        accessibilityState={{ disabled: !editable }}
        editable={editable}
        onBlur={(event) => {
          setFocused(false);
          onBlur?.(event);
        }}
        onFocus={(event) => {
          setFocused(true);
          onFocus?.(event);
        }}
        placeholderTextColor={theme.colors.foregroundDisabled}
        selectionColor={theme.colors.accent}
        style={[
          styles.control,
          focused && styles.focused,
          errorText && styles.invalid,
          !editable && styles.disabled,
        ]}
      />
      {description ? (
        <AppText
          accessibilityLiveRegion={errorText ? "assertive" : "none"}
          tone={errorText ? "error" : "subtle"}
          variant="caption"
          style={styles.description}
        >
          {description}
        </AppText>
      ) : null}
    </View>
  );
}

export interface AppSelectorProps extends FieldCopyProps {
  value: string;
  onPress: () => void;
  disabled?: boolean;
  expanded?: boolean;
}

export function AppSelector({
  disabled = false,
  errorText,
  expanded = false,
  helperText,
  label,
  onPress,
  required = false,
  value,
}: AppSelectorProps) {
  const theme = useAchiwaveTheme();
  const styles = useThemeStyles(createStyles);
  const description = errorText ?? helperText;
  return (
    <View style={styles.field}>
      <AppText variant="label">
        {label}{required ? " (required)" : ""}
      </AppText>
      <Pressable
        accessibilityHint={description ?? "Opens available choices."}
        accessibilityLabel={`${label}${required ? ", required" : ""}`}
        accessibilityRole="button"
        accessibilityState={{ disabled, expanded }}
        accessibilityValue={{ text: value }}
        android_ripple={createAndroidRipple(theme.colors.surfacePressed)}
        disabled={disabled}
        onPress={onPress}
        style={({ pressed }) => [
          styles.control,
          styles.selector,
          pressed && styles.pressed,
          errorText && styles.invalid,
          disabled && styles.disabled,
        ]}
      >
        <AppText style={styles.selectorValue}>{value}</AppText>
        <MaterialCommunityIcons
          accessibilityElementsHidden
          color={theme.colors.foregroundMuted}
          importantForAccessibility="no-hide-descendants"
          name={expanded ? "chevron-up" : "chevron-down"}
          size={24}
        />
      </Pressable>
      {description ? (
        <AppText
          accessibilityLiveRegion={errorText ? "assertive" : "none"}
          tone={errorText ? "error" : "subtle"}
          variant="caption"
          style={styles.description}
        >
          {description}
        </AppText>
      ) : null}
    </View>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  field: { gap: spacing.xs },
  control: {
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderRadius: radii.md,
    borderWidth: borders.thin,
    color: theme.colors.foreground,
    minHeight: sizing.formControl,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    ...typography.body,
  },
  focused: { borderColor: theme.colors.focus, borderWidth: borders.selected },
  invalid: { borderColor: theme.colors.error, borderWidth: borders.selected },
  disabled: { backgroundColor: theme.colors.surfaceDisabled, opacity: 0.7 },
  description: { marginTop: -spacing.xxs },
  selector: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  selectorValue: { flex: 1, marginRight: spacing.sm },
  pressed: { backgroundColor: theme.colors.surfacePressed },
});
