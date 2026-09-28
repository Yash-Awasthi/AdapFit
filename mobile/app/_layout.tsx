import { Stack, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { View } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { ThemeProvider, useTheme } from "../src/services/theme";
import { QueryProvider } from "../src/services/query-provider";
import { DevSettingsProvider } from "../src/services/devSettings";
import { useUserStore } from "../src/stores";
import { useEffect } from "react";
import { LoadingScreen, SyncStatusBadge } from "../src/components";
import { startSyncDaemon } from "../src/services/sync";
import { getToken } from "../src/services/authToken";
import { getConsent, isBlocked } from "../src/services/privacy";

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
    startSyncDaemon();
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

  // The server refuses data calls until consent is current, a guardian has
  // agreed, or a scheduled deletion is cancelled; send the user where they can act.
  const userId = useUserStore((s) => s.userId);
  useEffect(() => {
    if (!hydrated || loading || !profile || !getToken()) return;
    getConsent().then((state) => {
      if (isBlocked(state)) router.replace("/privacy" as any);
    });
  }, [hydrated, loading, profile, userId, router]);

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
        <Stack.Screen name="login" options={{ headerShown: false, animation: "fade" }} />
        <Stack.Screen name="register" options={{ headerShown: false, animation: "slide_from_right" }} />
        <Stack.Screen name="onboarding-welcome" options={{ headerShown: false, animation: "fade" }} />
        <Stack.Screen name="onboarding" options={{ headerShown: false, animation: "fade" }} />
        <Stack.Screen name="workout-active" options={{ headerShown: false }} />
        <Stack.Screen name="workout-detail" options={{ headerShown: false }} />
        <Stack.Screen name="form-checker" options={{ headerShown: false }} />
        <Stack.Screen name="privacy" options={{ headerShown: false, gestureEnabled: false }} />
        <Stack.Screen name="legal" options={{ headerShown: false }} />
      </Stack>
      {profile && (
        <View style={{ position: "absolute", top: 96, right: 12 }} pointerEvents="none">
          <SyncStatusBadge />
        </View>
      )}
    </>
  );
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <GestureHandlerRootView style={{ flex: 1 }}>
        <ThemeProvider>
          <QueryProvider>
            <DevSettingsProvider>
              <RootStack />
            </DevSettingsProvider>
          </QueryProvider>
        </ThemeProvider>
      </GestureHandlerRootView>
    </SafeAreaProvider>
  );
}