import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import { Tabs } from "expo-router";

import { ROOT_DESTINATIONS } from "../../../src/navigation/rootDestinations";

export default function AuthenticatedTabsLayout() {
  return (
    <Tabs
      backBehavior="history"
      screenOptions={{
        headerShown: false,
        tabBarActiveBackgroundColor: "#2A475E",
        tabBarActiveTintColor: "#FFFFFF",
        tabBarHideOnKeyboard: true,
        tabBarInactiveTintColor: "#A7B8C6",
        tabBarLabelStyle: { fontSize: 12, fontWeight: "700" },
        tabBarStyle: {
          backgroundColor: "#1B2838",
          borderTopColor: "#36566F",
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
