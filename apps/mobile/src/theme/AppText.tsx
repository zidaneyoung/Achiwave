import type { ComponentProps } from "react";
import { Text } from "react-native";

import { useAchiwaveTheme } from "./ThemeProvider";
import { typography, type TypographyVariant } from "./tokens";

type TextTone =
  | "default"
  | "muted"
  | "subtle"
  | "accent"
  | "onAction"
  | "success"
  | "warning"
  | "error"
  | "info";

export interface AppTextProps extends ComponentProps<typeof Text> {
  tone?: TextTone;
  variant?: TypographyVariant;
}

export function AppText({
  style,
  tone = "default",
  variant = "body",
  ...props
}: AppTextProps) {
  const { colors } = useAchiwaveTheme();
  const toneColors: Record<TextTone, string> = {
    default: colors.foreground,
    muted: colors.foregroundMuted,
    subtle: colors.foregroundSubtle,
    accent: colors.accent,
    onAction: colors.onAction,
    success: colors.success,
    warning: colors.warning,
    error: colors.error,
    info: colors.info,
  };
  return (
    <Text
      {...props}
      style={[typography[variant], { color: toneColors[tone] }, style]}
    />
  );
}
