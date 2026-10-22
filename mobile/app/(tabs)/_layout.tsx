/**
 * Tab layout: the five sections plus More. Each section's landing screen lists
 * its screens (src/navigation/sections.ts); scripts/check-sections.mjs proves
 * every screen is listed once. Detail screens are pushed from the (screens)
 * stack, so opening a tile keeps the tab underneath and Back returns to it.
 */
import { Tabs } from "expo-router";
import { View, Text, StyleSheet, Platform } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { colors, spacing } from "../../src/theme";

const TABS = [
  { name: "index", title: "Today", icon: "sunny-outline", activeIcon: "sunny" },
  { name: "body-section", title: "Body", icon: "barbell-outline", activeIcon: "barbell" },
  { name: "mind-section", title: "Mind", icon: "bulb-outline", activeIcon: "bulb" },
  { name: "care-section", title: "Care", icon: "medkit-outline", activeIcon: "medkit" },
  { name: "community-section", title: "Community", icon: "people-outline", activeIcon: "people" },
  { name: "menu", title: "More", icon: "grid-outline", activeIcon: "grid" },
] as const;

function TabIcon({ icon, activeIcon, label, color, focused }: {
  icon: string; activeIcon: string; label: string; color: string; focused: boolean;
}) {
  return (
    <View style={styles.tabItem}>
      <View style={[styles.tabIcon, focused && { backgroundColor: color + "1F" }]}>
        <Ionicons name={(focused ? activeIcon : icon) as any} size={22} color={color} />
      </View>
      <Text
        style={[styles.tabLabel, { color }, focused && styles.tabLabelActive]}
        numberOfLines={1}
      >
        {label}
      </Text>
    </View>
  );
}

export default function TabLayout() {
  const insets = useSafeAreaInsets();

  // Gesture-navigation Android reports a small bottom inset and three-button
  // navigation a large one, so the bar height has to follow the measured inset.
  const bottomInset = Math.max(insets.bottom, Platform.OS === "ios" ? 20 : 8);

  return (
    <Tabs
      screenOptions={{
        tabBarStyle: {
          position: "absolute",
          backgroundColor: "rgb(12, 17, 28)",
          borderTopWidth: StyleSheet.hairlineWidth,
          borderTopColor: colors.surface.border,
          height: 58 + bottomInset,
          paddingBottom: bottomInset,
          paddingTop: 6,
          paddingHorizontal: spacing.xs,
          elevation: 0,
          shadowOpacity: 0,
        },
        tabBarShowLabel: false,
        tabBarItemStyle: { paddingVertical: 0 },
        tabBarActiveTintColor: colors.primaryLight,
        tabBarInactiveTintColor: colors.text.muted,
        headerShown: false,
        sceneStyle: { backgroundColor: colors.bg.deep },
      }}
    >
      {TABS.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{
            title: tab.title,
            tabBarAccessibilityLabel: tab.title,
            tabBarIcon: ({ focused }) => (
              <TabIcon
                icon={tab.icon}
                activeIcon={tab.activeIcon}
                label={tab.title}
                color={focused ? colors.primaryLight : colors.text.muted}
                focused={focused}
              />
            ),
          }}
        />
      ))}
    </Tabs>
  );
}

const styles = StyleSheet.create({
  // Six tabs must fit a 360 dp screen.
  tabItem: { alignItems: "center", justifyContent: "center", width: 58, gap: 2 },
  tabIcon: {
    width: 40,
    height: 28,
    borderRadius: 10,
    justifyContent: "center",
    alignItems: "center",
  },
  tabLabel: { fontSize: 10, fontWeight: "600", letterSpacing: 0.2 },
  tabLabelActive: { fontWeight: "700" },
});
