import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import { Tabs } from "expo-router";

import {
  AUTHENTICATED_TAB_BACK_BEHAVIOR,
  AUTHENTICATED_TAB_INITIAL_ROUTE,
} from "../../../src/navigation/backBehavior";
import { ROOT_DESTINATIONS } from "../../../src/navigation/rootDestinations";
import { useAchiwaveTheme } from "../../../src/theme/ThemeProvider";
import { typography } from "../../../src/theme/tokens";

export default function AuthenticatedTabsLayout() {
  const theme = useAchiwaveTheme();
  return (
    <Tabs
      backBehavior={AUTHENTICATED_TAB_BACK_BEHAVIOR}
      initialRouteName={AUTHENTICATED_TAB_INITIAL_ROUTE}
      screenOptions={{
        headerShown: false,
        sceneStyle: { backgroundColor: theme.colors.background },
        tabBarActiveBackgroundColor: theme.colors.surfaceElevated,
        tabBarActiveTintColor: theme.colors.foreground,
        tabBarHideOnKeyboard: true,
        tabBarInactiveTintColor: theme.colors.foregroundMuted,
        tabBarLabelStyle: { ...typography.caption, fontWeight: "700" },
        tabBarStyle: {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.border,
        },
      }}
    >
      {ROOT_DESTINATIONS.map((destination) => (
        <Tabs.Screen
          key={destination.name}
          name={destination.name}
          options={{
            tabBarAccessibilityLabel: destination.accessibilityLabel,
            tabBarIcon: ({ color, focused, size }) => (
              <MaterialCommunityIcons
                accessibilityElementsHidden
                color={color}
                importantForAccessibility="no-hide-descendants"
                name={focused ? destination.selectedIcon : destination.icon}
                size={size}
              />
            ),
            title: destination.label,
          }}
        />
      ))}
    </Tabs>
  );
}
