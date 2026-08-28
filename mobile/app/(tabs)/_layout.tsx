import { Tabs, useRouter } from "expo-router";
import { TouchableOpacity } from "react-native";
import { Heart, Dumbbell, TrendingUp, MessageCircle, LayoutGrid, ChevronLeft } from "lucide-react-native";
import { useTheme } from "../../src/services/theme";

function BackButton() {
  const router = useRouter();
  const { theme } = useTheme();
  return (
    <TouchableOpacity onPress={() => router.back()} hitSlop={12} style={{ paddingHorizontal: 8 }}>
      <ChevronLeft size={24} color={theme.text} />
    </TouchableOpacity>
  );
}

const PUSHED_SCREENS = [
  "exercises", "wellness", "sleep", "nutrition", "health", "diet",
  "stats", "social", "periodization", "achievements", "settings", "cycle",
];

export default function TabLayout() {
  const { theme } = useTheme();

  return (
    <Tabs
      screenOptions={{
        tabBarStyle: {
          backgroundColor: theme.surface,
          borderTopColor: theme.border,
          borderTopWidth: 1,
          height: 64,
          paddingBottom: 10,
          paddingTop: 8,
        },
        tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
        tabBarActiveTintColor: theme.primaryLight,
        tabBarInactiveTintColor: theme.textMuted,
        headerShown: false,
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Home", tabBarIcon: ({ color, size }) => <Heart size={size} color={color} /> }} />
      <Tabs.Screen name="workout" options={{ title: "Workout", tabBarIcon: ({ color, size }) => <Dumbbell size={size} color={color} /> }} />
      <Tabs.Screen name="chat" options={{ title: "Coach", tabBarIcon: ({ color, size }) => <MessageCircle size={size} color={color} /> }} />
      <Tabs.Screen name="trends" options={{ title: "Trends", tabBarIcon: ({ color, size }) => <TrendingUp size={size} color={color} /> }} />
      <Tabs.Screen name="menu" options={{ title: "Menu", tabBarIcon: ({ color, size }) => <LayoutGrid size={size} color={color} /> }} />

      {/* Routable but not shown in the bar — reached from the Menu catalog.
          Screens already render their own big title, so the native header
          is transparent and only supplies the back chevron. */}
      {PUSHED_SCREENS.map((name) => (
        <Tabs.Screen
          key={name}
          name={name}
          options={{
            href: null,
            headerShown: true,
            headerTitle: "",
            headerTransparent: true,
            headerShadowVisible: false,
            headerLeft: () => <BackButton />,
          }}
        />
      ))}
      {/* these render their own in-screen back headers */}
      <Tabs.Screen name="profile" options={{ href: null }} />
      <Tabs.Screen name="personal-info" options={{ href: null }} />
      <Tabs.Screen name="dev-tools" options={{ href: null }} />
    </Tabs>
  );
}
