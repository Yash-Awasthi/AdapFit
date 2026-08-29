/**
 * Tab Layout — Premium Glassmorphism Tab Bar
 * Modern bottom navigation with frosted glass effect
 */
import { Tabs, useRouter } from "expo-router";
import { TouchableOpacity, View, StyleSheet, Platform } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors, spacing, radius, glass } from "../../src/theme";

function BackButton() {
  const router = useRouter();
  return (
    <TouchableOpacity onPress={() => router.back()} hitSlop={12} style={{ paddingHorizontal: 8 }}>
      <Ionicons name="chevron-back" size={24} color={colors.text.primary} />
    </TouchableOpacity>
  );
}

const HIDDEN_SCREENS = [
  "telemedicine", "forums", "analytics", "vital-signs", "gamification",
  "family", "health-calendar", "recipes", "exercises", "wellness", "sleep",
  "nutrition", "health", "diet", "stats", "social", "periodization",
  "achievements", "settings", "cycle", "profile", "personal-info", "dev-tools",
  "sleep-tracker", "nutrition-log", "mental-health", "medication", "emergency",
  "community", "workouts", "devices", "coach", "voice-health", "longevity",
  "ambient", "data-export", "diabetes", "pregnancy", "chronic-pain", "fertility",
  "accessibility-settings", "menu",
  "skin-health", "circadian", "posture", "respiratory",
  "medical-imaging", "remote-monitoring",
  "genomics", "cardiac-rehab", "addiction-recovery",
  "health-equity", "health-savings", "precision-nutrition",
  "recovery-dashboard",
];

const screenHeaderStyle = {
  headerShown: true,
  headerTitle: "",
  headerTransparent: true,
  headerShadowVisible: false,
  headerStyle: { backgroundColor: "transparent" },
  headerTintColor: colors.text.primary,
  headerLeft: () => <BackButton />,
};

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarStyle: {
          position: "absolute" as const,
          backgroundColor: "rgba(15, 22, 41, 0.88)",
          borderTopWidth: 0.5,
          borderTopColor: "rgba(255, 255, 255, 0.08)",
          height: 70,
          paddingBottom: Platform.OS === "ios" ? 24 : 10,
          paddingTop: 8,
          elevation: 0,
          shadowOpacity: 0,
        },
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: "600" as const,
          marginTop: 2,
        },
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.text.muted,
        headerShown: false,
      }}
    >
      {/* Main Tabs */}
      <Tabs.Screen
        name="dashboard"
        options={{
          title: "Dashboard",
          tabBarIcon: ({ color, size }) => (
            <View style={[styles.tabIconContainer, { backgroundColor: color + "15" }]}>
              <Ionicons name="grid" size={20} color={color} />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="index"
        options={{
          title: "Home",
          tabBarIcon: ({ color, size }) => (
            <View style={[styles.tabIconContainer, { backgroundColor: color + "15" }]}>
              <Ionicons name="home" size={20} color={color} />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="workout"
        options={{
          title: "Workout",
          tabBarIcon: ({ color, size }) => (
            <View style={[styles.tabIconContainer, { backgroundColor: color + "15" }]}>
              <Ionicons name="barbell" size={20} color={color} />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="health-hub"
        options={{
          title: "Health",
          tabBarIcon: ({ color, size }) => (
            <View style={[styles.tabIconContainer, { backgroundColor: color + "15" }]}>
              <Ionicons name="pulse" size={20} color={color} />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="chat"
        options={{
          title: "Coach",
          tabBarIcon: ({ color, size }) => (
            <View style={[styles.tabIconContainer, { backgroundColor: color + "15" }]}>
              <Ionicons name="chatbubble-ellipses" size={20} color={color} />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="content-feed"
        options={{
          title: "Content",
          tabBarIcon: ({ color, size }) => (
            <View style={[styles.tabIconContainer, { backgroundColor: color + "15" }]}>
              <Ionicons name="play-circle" size={20} color={color} />
            </View>
          ),
        }}
      />

      {/* Trending Tab */}
      <Tabs.Screen
        name="trends"
        options={{
          title: "Trends",
          tabBarIcon: ({ color, size }) => (
            <View style={[styles.tabIconContainer, { backgroundColor: color + "15" }]}>
              <Ionicons name="trending-up" size={20} color={color} />
            </View>
          ),
        }}
      />

      {/* Hidden screens with headers */}
      {HIDDEN_SCREENS.map((name) => (
        <Tabs.Screen
          key={name}
          name={name}
          options={{
            href: null,
            ...screenHeaderStyle,
          }}
        />
      ))}
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
  },
});
