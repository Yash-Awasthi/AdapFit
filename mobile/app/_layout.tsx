import { Stack, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { Pressable, Text, View } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { ThemeProvider, useTheme } from "../src/services/theme";
import { QueryProvider } from "../src/services/query-provider";
import { DevSettingsProvider } from "../src/services/devSettings";
import { useUserStore } from "../src/stores";
import { useEffect } from "react";
import { LoadingScreen, SyncStatusBadge } from "../src/components";
import { ConnectionBanner } from "../src/components/ConnectionBanner";
import { startSyncDaemon } from "../src/services/sync";
import { getToken } from "../src/services/authToken";
import { getConsent, isBlocked } from "../src/services/privacy";
import { syncHealthConnectIfDue } from "../src/services/healthConnect";
import { applyReminders } from "../src/services/reminders";
import { installCrashReporting, reportError } from "../src/services/crashReport";
// Registers the background location task; must load before any run starts or resumes.
import "../src/services/runTracker";

installCrashReporting();

/** A render error in any screen: report it and offer a retry instead of a blank app. */
export function ErrorBoundary({ error, retry }: { error: Error; retry: () => Promise<void> }) {
  useEffect(() => reportError(error), [error]);
  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center", padding: 24, gap: 16 }}>
      <Text style={{ fontSize: 18, fontWeight: "600", textAlign: "center" }}>Something went wrong on this screen.</Text>
      <Pressable accessibilityRole="button" onPress={retry} style={{ paddingVertical: 12, paddingHorizontal: 24, borderRadius: 8, backgroundColor: "#2563eb" }}>
        <Text style={{ color: "#fff", fontWeight: "600" }}>Try again</Text>
      </Pressable>
    </View>
  );
}

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

  // Signed out: sign-in (or sign-up and the documents it links to). Signed in
  // without a profile: onboarding. Waits for hydration so a profile fetch in
  // flight is not misread as "no profile".
  const signedIn = useUserStore((s) => s.signedIn);
  useEffect(() => {
    if (!hydrated || loading) return;
    const onOnboarding = segments[0] === "onboarding-welcome";
    if (!signedIn) {
      if (!["login", "register", "legal"].includes(segments[0] as string)) router.replace("/login" as any);
    } else if (!profile && !onOnboarding) {
      router.replace("/onboarding-welcome");
    } else if (profile && onOnboarding) {
      router.replace("/(tabs)");
    }
  }, [hydrated, loading, signedIn, profile, segments, router]);

  // The server refuses data calls until consent is current, a guardian has
  // agreed, or a scheduled deletion is cancelled; send the user where they can act.
  const userId = useUserStore((s) => s.userId);
  useEffect(() => {
    if (!hydrated || loading || !profile || !getToken()) return;
    getConsent().then((state) => {
      if (isBlocked(state)) router.replace("/privacy" as any);
      else {
        syncHealthConnectIfDue();
        applyReminders(false);
      }
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
      <ConnectionBanner />
      {profile && segments[0] !== "sleep-sounds" && (
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