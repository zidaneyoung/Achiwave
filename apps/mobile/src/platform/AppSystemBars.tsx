import { useEffect, useMemo } from "react";
import * as NavigationBar from "expo-navigation-bar";
import { Platform, StatusBar } from "react-native";

import { safeConsole } from "../security/safeLogging";
import { useAchiwaveTheme } from "../theme/ThemeProvider";
import { resolveSystemBarAppearance } from "./systemBars";

export function AppSystemBars() {
  const theme = useAchiwaveTheme();
  const appearance = useMemo(
    () => resolveSystemBarAppearance(theme.mode),
    [theme.mode],
  );

  useEffect(() => {
    if (Platform.OS !== "android") {
      return;
    }
    try {
      NavigationBar.setStyle(appearance.navigationButtonStyle);
    } catch {
      safeConsole.warn("navigation_bar_style_unavailable");
    }
  }, [appearance.navigationButtonStyle]);

  return (
    <StatusBar
      animated={false}
      backgroundColor="transparent"
      barStyle={appearance.statusBarStyle}
      translucent
    />
  );
}
