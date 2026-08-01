import { useState } from "react";
import type { ComponentProps } from "react";
import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  View,
  type PressableProps,
} from "react-native";

import { AppText } from "../theme/AppText";
import {
  type AchiwaveTheme,
  useAchiwaveTheme,
  useThemeStyles,
} from "../theme/ThemeProvider";
import { borders, radii, sizing, spacing } from "../theme/tokens";

type IconName = ComponentProps<typeof MaterialCommunityIcons>["name"];
export type ButtonVariant =
  | "primary"
  | "secondary"
  | "ghost"
  | "destructive";

export interface AppButtonProps extends Omit<PressableProps, "children" | "style"> {
  label: string;
  variant?: ButtonVariant;
  icon?: IconName;
  iconOnly?: boolean;
  loading?: boolean;
}

export function AppButton({
  accessibilityHint,
  disabled = false,
  icon,
  iconOnly = false,
  label,
  loading = false,
  onBlur,
  onFocus,
  variant = "primary",
  ...pressableProps
}: AppButtonProps) {
  const theme = useAchiwaveTheme();
  const styles = useThemeStyles(createStyles);
  const [focused, setFocused] = useState(false);
  const unavailable = disabled || loading;
  const foreground =
    variant === "primary" || variant === "destructive"
      ? theme.colors.onAction
      : theme.colors.foreground;

  return (
    <Pressable
      {...pressableProps}
      accessibilityHint={accessibilityHint}
      accessibilityLabel={label}
      accessibilityRole="button"
      accessibilityState={{ busy: loading, disabled: unavailable }}
      android_ripple={{ color: theme.colors.surfacePressed }}
      disabled={unavailable}
      onBlur={(event) => {
        setFocused(false);
        onBlur?.(event);
      }}
      onFocus={(event) => {
        setFocused(true);
        onFocus?.(event);
      }}
      style={({ pressed }) => [
        styles.base,
        iconOnly && styles.iconOnly,
        styles[variant],
        pressed && styles[`${variant}Pressed`],
        focused && styles.focused,
        unavailable && styles.disabled,
      ]}
    >
      {loading ? (
        <ActivityIndicator accessibilityElementsHidden color={foreground} />
      ) : (
        <View accessibilityElementsHidden style={styles.content}>
          {icon ? (
            <MaterialCommunityIcons color={foreground} name={icon} size={20} />
          ) : null}
          {iconOnly ? null : (
            <AppText
              tone={variant === "primary" || variant === "destructive" ? "onAction" : "default"}
              variant="label"
            >
              {label}
            </AppText>
          )}
        </View>
      )}
    </Pressable>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  base: {
    alignItems: "center",
    borderRadius: radii.md,
    borderWidth: borders.thin,
    justifyContent: "center",
    minHeight: sizing.minimumTouchTarget,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  content: { alignItems: "center", flexDirection: "row", gap: spacing.xs },
  iconOnly: {
    minWidth: sizing.minimumTouchTarget,
    paddingHorizontal: spacing.sm,
  },
  primary: { backgroundColor: theme.colors.action, borderColor: theme.colors.action },
  primaryPressed: { backgroundColor: theme.colors.actionPressed },
  secondary: { backgroundColor: "transparent", borderColor: theme.colors.borderStrong },
  secondaryPressed: { backgroundColor: theme.colors.surfacePressed },
  ghost: { backgroundColor: "transparent", borderColor: "transparent" },
  ghostPressed: { backgroundColor: theme.colors.surfacePressed },
  destructive: { backgroundColor: theme.colors.danger, borderColor: theme.colors.danger },
  destructivePressed: { backgroundColor: theme.colors.dangerPressed },
  focused: { borderColor: theme.colors.focus, borderWidth: borders.selected },
  disabled: { opacity: 0.55 },
});
