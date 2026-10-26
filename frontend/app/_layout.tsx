import { Stack, useRouter, useSegments } from "expo-router";
import { useEffect } from "react";
import { useFonts } from "expo-font";
import { LogBox, StyleSheet } from "react-native";
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
    "RobotoMono-400": require("../assets/website-2026-10-26/roboto-mono-latin-400-normal.ttf"),
    "RobotoMono-500": require("../assets/website-2026-10-26/roboto-mono-latin-500-normal.ttf"),
    "RobotoMono-600": require("../assets/website-2026-10-26/roboto-mono-latin-600-normal.ttf"),
    "RobotoMono-700": require("../assets/website-2026-10-26/roboto-mono-latin-700-normal.ttf"),
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
            <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.surface }, animation: "slide_from_right" }}>
              <Stack.Screen name="attempt/[id]" options={{ gestureEnabled: false }} />
              <Stack.Screen name="rapid/session" options={{ gestureEnabled: false, animation: "fade_from_bottom" }} />
            </Stack>
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
    if (ready && !user && first && first !== "entry") router.replace("/entry");
  }, [ready, user, segments, router]);
  return null;
}

const styles = StyleSheet.create({ root: { flex: 1 } });
