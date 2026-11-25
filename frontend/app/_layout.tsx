import { ARENA, HOME_ROUTE, arenaAllows } from "@/src/arenaMode"; // first: the browser arena sets up its column before any screen measures the window
import { Stack, usePathname, useRouter, useSegments } from "expo-router";
import { useEffect } from "react";
import { useFonts } from "expo-font";
import { ActivityIndicator, LogBox, StyleSheet, View } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { KeyboardProvider } from "react-native-keyboard-controller";
import { StatusBar } from "expo-status-bar";

import { ErrorBoundary } from "@/src/components/error-boundary";
import { AuthProvider, useAuth } from "@/src/auth";
import { InboxPoller, isRoomPath } from "@/src/rapid/social";
import { SmoothMode } from "@/src/analysis/smooth";
import { MatchedGate } from "@/src/matched/gate";
import { colors } from "@/src/theme";

// "matched" (JEE Main questions that matched ours) is open to people who have not signed in.
const PUBLIC_ROUTES = ["entry", "forgot-pin", "privacy", "delete-account", "matched"];

LogBox.ignoreAllLogs(true);

export default function RootLayout() {
  // Prewarm brand + icon fonts so icons render on first paint (Expo Go Android).
  const [loaded, failed] = useFonts({
    "Figtree-400": require("../assets/website-2026-10-26/figtree-latin-400-normal.ttf"),
    "Figtree-500": require("../assets/website-2026-10-26/figtree-latin-500-normal.ttf"),
    "Figtree-600": require("../assets/website-2026-10-26/figtree-latin-600-normal.ttf"),
    "Figtree-700": require("../assets/website-2026-10-26/figtree-latin-700-normal.ttf"),
    "Figtree-800": require("../assets/website-2026-10-26/figtree-latin-800-normal.ttf"),
    // The website's number face (scores, ranks, times in the analysis).
    "RobotoMono-400": require("../assets/website-2026-10-26/roboto-mono-latin-400-normal.ttf"),
    "RobotoMono-700": require("../assets/website-2026-10-26/roboto-mono-latin-700-normal.ttf"),
    MaterialDesignIcons: require("@react-native-vector-icons/material-design-icons/fonts/MaterialDesignIcons.ttf"),
  });
  if (!loaded && !failed) return null;

  return (
    <GestureHandlerRootView style={styles.root}>
      <ErrorBoundary>
        <AuthProvider>
          <KeyboardProvider>
            <StatusBar style="dark" />
            <AuthGate />
            <InboxPoller />
            <SmoothMode />
            <MatchedGate />
            <SessionBoundary><Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.surface }, animation: "slide_from_right" }}>
              <Stack.Screen name="attempt/[id]" options={{ gestureEnabled: false }} />
              <Stack.Screen name="rapid/session" options={{ gestureEnabled: false, animation: "fade_from_bottom" }} />
              <Stack.Screen name="rapid/daily" options={{ gestureEnabled: false, animation: "fade_from_bottom" }} />
              <Stack.Screen name="rapid/duel" options={{ gestureEnabled: false, animation: "fade" }} />
              <Stack.Screen name="rapid/room/[cid]" options={{ gestureEnabled: false, animation: "fade_from_bottom" }} />
            </Stack></SessionBoundary>
          </KeyboardProvider>
        </AuthProvider>
      </ErrorBoundary>
    </GestureHandlerRootView>
  );
}

// Signed-out users opening any inner route are sent to entry (no endless placeholders). A match link comes back to its room after sign-in.
// The browser arena is Rapid Fire only: tests stay on the website, so their routes lead back to the lobby.
function AuthGate() {
  const { user, ready } = useAuth();
  const segments = useSegments();
  const pathname = usePathname();
  const router = useRouter();
  useEffect(() => {
    const first = segments[0] as string | undefined;
    if (ready && !user && first && !PUBLIC_ROUTES.includes(first)) router.replace(isRoomPath(pathname) ? { pathname: "/entry", params: { next: pathname } } : "/entry");
    else if (ARENA && ready && user && !arenaAllows(segments as string[])) router.replace(HOME_ROUTE);
  }, [ready, user, segments, pathname, router]);
  return null;
}

function SessionBoundary({ children }: { children: React.ReactNode }) {
  const { ready, user } = useAuth();
  const segments = useSegments();
  const first = segments[0] as string;
  const publicScreen = PUBLIC_ROUTES.includes(first);
  // Public help/entry/policy must stay usable while the account server connects.
  // Private routes remain covered until a verified session has settled.
  // In the browser arena a test route is never shown, not even for the moment before it leads back to the lobby.
  const blocked = (!publicScreen && (!ready || !user)) || (ARENA && !arenaAllows(segments as string[]));
  // Keep the root navigator mounted (required for Expo deep links), but never
  // expose a private route while validating or redirecting an expired session.
  return <View style={styles.root}>
    <View style={[styles.root, blocked && styles.hidden]} pointerEvents={blocked ? "none" : "auto"} accessibilityElementsHidden={blocked} importantForAccessibility={blocked ? "no-hide-descendants" : "auto"}>{children}</View>
    {blocked ? <View testID="session-verifying" style={styles.verifying}><ActivityIndicator testID="session-verifying-spinner" color={colors.brandPrimary} accessibilityLabel="Checking your session" /></View> : null}
  </View>;
}

const styles = StyleSheet.create({ root: { flex: 1 }, hidden: { opacity: 0 }, verifying: { position: "absolute", top: 0, left: 0, bottom: 0, right: 0, alignItems: "center", justifyContent: "center", backgroundColor: colors.surface } });
