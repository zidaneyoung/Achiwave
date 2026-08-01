import type { ColorSchemeName, StatusBarStyle } from "react-native";

export interface SystemBarAppearance {
  statusBarStyle: StatusBarStyle;
  navigationButtonStyle: "light" | "dark";
}

export function resolveSystemBarAppearance(
  colorScheme: ColorSchemeName,
): SystemBarAppearance {
  if (colorScheme === "light") {
    return {
      statusBarStyle: "dark-content",
      navigationButtonStyle: "dark",
    };
  }
  return {
    statusBarStyle: "light-content",
    navigationButtonStyle: "light",
  };
}
