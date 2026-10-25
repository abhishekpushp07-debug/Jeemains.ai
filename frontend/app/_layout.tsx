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
    "Jakarta-400": require("../assets/fonts/PlusJakartaSans-400.ttf"),
    "Jakarta-500": require("../assets/fonts/PlusJakartaSans-500.ttf"),
    "Jakarta-600": require("../assets/fonts/PlusJakartaSans-600.ttf"),
    "Jakarta-700": require("../assets/fonts/PlusJakartaSans-700.ttf"),
    "Jakarta-800": require("../assets/fonts/PlusJakartaSans-800.ttf"),
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
