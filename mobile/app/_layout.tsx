import { Stack, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { ThemeProvider, useTheme } from "../src/services/theme";
import { DevSettingsProvider } from "../src/services/devSettings";
import { useUserStore } from "../src/stores";
import { useEffect } from "react";
import { LoadingScreen } from "../src/components";

function RootStack() {
  const { theme, isDark } = useTheme();
  const hydrate = useUserStore((s) => s.hydrate);
  const hydrated = useUserStore((s) => s.hydrated);
  const loading = useUserStore((s) => s.loading);
  const profile = useUserStore((s) => s.profile);
  const router = useRouter();
  const segments = useSegments();

  // Load the persisted user identity once at startup so every screen
  // (and the gender-aware tab bar) reads the same user id.
  useEffect(() => {
    hydrate();
  }, [hydrate]);

  // Route new (no saved profile) users to onboarding, everyone else to the
  // app. Waits for hydration to finish so an existing user's profile fetch
  // in flight doesn't get misread as "no account" and bounce them back.
  useEffect(() => {
    if (!hydrated || loading) return;
    const onOnboarding = segments[0] === "onboarding-welcome";
    if (!profile && !onOnboarding) {
      router.replace("/onboarding-welcome");
    } else if (profile && onOnboarding) {
      router.replace("/(tabs)");
    }
  }, [hydrated, loading, profile, segments, router]);

  if (!hydrated || loading) {
    return <LoadingScreen />;
  }

  return (
    <>
      <StatusBar style={isDark ? "light" : "dark"} />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: theme.background },
          animation: "slide_from_right",
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="onboarding-welcome" options={{ headerShown: false, animation: "fade" }} />
        <Stack.Screen name="onboarding" options={{ headerShown: false, animation: "fade" }} />
        <Stack.Screen name="workout-active" options={{ headerShown: false }} />
        <Stack.Screen name="workout-detail" options={{ headerShown: false }} />
        <Stack.Screen name="form-checker" options={{ headerShown: false }} />
      </Stack>
    </>
  );
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ThemeProvider>
        <DevSettingsProvider>
          <RootStack />
        </DevSettingsProvider>
      </ThemeProvider>
    </GestureHandlerRootView>
  );
}