import type { ReactNode } from "react";
import { createContext, useContext, useMemo } from "react";
import { useColorScheme, type ColorSchemeName } from "react-native";

import { DARK_COLORS, LIGHT_COLORS, type ThemeColors } from "./colors";

export type ThemeMode = "light" | "dark";

export interface AchiwaveTheme {
  mode: ThemeMode;
  dark: boolean;
  colors: ThemeColors;
}

const THEMES: Readonly<Record<ThemeMode, AchiwaveTheme>> = {
  dark: { mode: "dark", dark: true, colors: DARK_COLORS },
  light: { mode: "light", dark: false, colors: LIGHT_COLORS },
};

const ThemeContext = createContext<AchiwaveTheme | null>(null);

export function resolveTheme(mode: ColorSchemeName) {
  return THEMES[mode === "light" ? "light" : "dark"];
}

export function AchiwaveThemeProvider({ children }: { children: ReactNode }) {
  const systemMode = useColorScheme();
  const theme = resolveTheme(systemMode);
  return <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>;
}

export function useAchiwaveTheme(): AchiwaveTheme {
  const context = useContext(ThemeContext);
  const systemMode = useColorScheme();
  return context ?? resolveTheme(systemMode);
}

export function useThemeStyles<T>(factory: (theme: AchiwaveTheme) => T): T {
  const theme = useAchiwaveTheme();
  return useMemo(() => factory(theme), [factory, theme]);
}
