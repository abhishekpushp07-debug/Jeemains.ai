import { Stack, useRouter, useSegments } from "expo-router";
import { useEffect } from "react";
import { useFonts } from "expo-font";
import { ActivityIndicator, LogBox, StyleSheet, View } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { KeyboardProvider } from "react-native-keyboard-controller";
import { StatusBar } from "expo-status-bar";

import { ErrorBoundary } from "@/src/components/error-boundary";
import { AuthProvider, useAuth } from "@/src/auth";
import { colors } from "@/src/theme";

LogBox.ignoreAllLogs(true);

export default function RootLayout() {
  // Prewarm brand + icon fonts so icons render on first paint (Expo Go Android).
  const [loaded, failed] = useFonts({
    "Figtree-400": require("../assets/website-2026-10-26/figtree-latin-400-normal.ttf"),
    "Figtree-500": require("../assets/website-2026-10-26/figtree-latin-500-normal.ttf"),
    "Figtree-600": require("../assets/website-2026-10-26/figtree-latin-600-normal.ttf"),
    "Figtree-700": require("../assets/website-2026-10-26/figtree-latin-700-normal.ttf"),
    "Figtree-800": require("../assets/website-2026-10-26/figtree-latin-800-normal.ttf"),
    MaterialDesignIcons: require("@react-native-vector-icons/material-design-icons/fonts/MaterialDesignIcons.ttf"),
  });
  if (!loaded && !failed) return null;

  return (
    <GestureHandlerRootView style={styles.root}>
      <ErrorBoundary>
        <AuthProvider>
          <KeyboardProvider>
            <StatusBar style="light" />
            <AuthGate />
            <SessionBoundary><Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.surface }, animation: "slide_from_right" }}>
              <Stack.Screen name="attempt/[id]" options={{ gestureEnabled: false }} />
              <Stack.Screen name="rapid/session" options={{ gestureEnabled: false, animation: "fade_from_bottom" }} />
            </Stack></SessionBoundary>
          </KeyboardProvider>
        </AuthProvider>
      </ErrorBoundary>
    </GestureHandlerRootView>
  );
}

// Signed-out users opening any inner route are sent to entry (no endless placeholders).
function AuthGate() {
  const { user, ready } = useAuth();
  const segments = useSegments();
  const router = useRouter();
  useEffect(() => {
    const first = segments[0] as string | undefined;
    if (ready && !user && first && !["entry", "forgot-pin"].includes(first)) router.replace("/entry");
  }, [ready, user, segments, router]);
  return null;
}

function SessionBoundary({ children }: { children: React.ReactNode }) {
  const { ready, user } = useAuth();
  const segments = useSegments();
  const publicScreen = ["entry", "forgot-pin"].includes(segments[0] as string);
  const blocked = !ready || (!user && !publicScreen);
  // Keep the root navigator mounted (required for Expo deep links), but never
  // expose a private route while validating or redirecting an expired session.
  return <View style={styles.root}>
    <View style={[styles.root, blocked && styles.hidden]} pointerEvents={blocked ? "none" : "auto"} accessibilityElementsHidden={blocked} importantForAccessibility={blocked ? "no-hide-descendants" : "auto"}>{children}</View>
    {blocked ? <View testID="session-verifying" style={styles.verifying}><ActivityIndicator testID="session-verifying-spinner" color={colors.brandPrimary} accessibilityLabel="Checking your session" /></View> : null}
  </View>;
}

const styles = StyleSheet.create({ root: { flex: 1 }, hidden: { opacity: 0 }, verifying: { position: "absolute", top: 0, left: 0, bottom: 0, right: 0, alignItems: "center", justifyContent: "center", backgroundColor: colors.surface } });
