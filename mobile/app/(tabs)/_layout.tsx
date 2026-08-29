/**
 * Tab layout.
 *
 * Five primary destinations. Everything else is reachable through the More
 * catalog, which is where the previous seven-tab bar was crushing its labels.
 */
import { Tabs } from "expo-router";
import { View, Text, StyleSheet, Platform } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { colors, spacing } from "../../src/theme";
import { BackButton } from "../../src/components/BackButton";

const TABS = [
  { name: "index", title: "Home", icon: "home", activeIcon: "home" },
  { name: "workout", title: "Train", icon: "barbell-outline", activeIcon: "barbell" },
  { name: "content-feed", title: "Watch", icon: "play-circle-outline", activeIcon: "play-circle" },
  { name: "chat", title: "Coach", icon: "chatbubble-ellipses-outline", activeIcon: "chatbubble-ellipses" },
  { name: "menu", title: "More", icon: "grid-outline", activeIcon: "grid" },
] as const;

const HIDDEN_SCREENS = [
  "dashboard", "health-hub", "trends",
  "telemedicine", "forums", "analytics", "vital-signs", "gamification",
  "family", "health-calendar", "recipes", "exercises", "wellness", "sleep",
  "nutrition", "health", "stats", "social", "periodization",
  "achievements", "settings", "personal-info", "dev-tools",
  "sleep-tracker", "mental-health", "medication", "emergency",
  "community", "workouts", "devices", "coach", "voice-health", "longevity",
  "ambient", "data-export", "diabetes", "chronic-pain", "chronic-pain-v2",
  "accessibility-settings",
  "skin-health", "circadian", "posture", "respiratory",
  "medical-imaging", "remote-monitoring",
  "genomics", "cardiac-rehab", "addiction-recovery",
  "health-equity", "health-savings", "precision-nutrition",
];

/** Only meaningful when the profile records a female gender. */
const FEMALE_SCREENS = ["cycle", "fertility", "pregnancy", "pregnancy-v2"];

const screenHeaderStyle = {
  headerShown: true,
  headerTitle: "",
  headerTransparent: true,
  headerShadowVisible: false,
  headerStyle: { backgroundColor: "transparent" },
  headerTintColor: colors.text.primary,
  headerLeft: () => <BackButton />,
};

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
          backgroundColor: "rgba(12, 17, 28, 0.94)",
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
            tabBarIcon: ({ color, focused }) => (
              <TabIcon
                icon={tab.icon}
                activeIcon={tab.activeIcon}
                label={tab.title}
                color={color}
                focused={focused}
              />
            ),
          }}
        />
      ))}

      {HIDDEN_SCREENS.map((name) => (
        <Tabs.Screen key={name} name={name} options={{ href: null, ...screenHeaderStyle }} />
      ))}

      {/*
        These routes stay registered so a saved deep link still resolves after
        a profile change. What gates them is the More catalog, which only
        lists them when useFemaleFeatures() is true.
      */}
      {FEMALE_SCREENS.map((name) => (
        <Tabs.Screen key={name} name={name} options={{ href: null, ...screenHeaderStyle }} />
      ))}
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabItem: { alignItems: "center", justifyContent: "center", width: 64, gap: 2 },
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
