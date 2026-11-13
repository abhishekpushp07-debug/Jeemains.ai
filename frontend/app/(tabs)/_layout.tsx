import React, { useEffect } from "react";
import { Image, Platform, StyleProp, StyleSheet, View, ViewStyle, useWindowDimensions } from "react-native";
import Animated, { Easing, cancelAnimation, useAnimatedStyle, useReducedMotion, useSharedValue, withRepeat, withSequence, withTiming } from "react-native-reanimated";
import { Tabs, useSegments } from "expo-router";
import { NativeTabs } from "expo-router/native-tabs";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { IconName, Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { colors, space } from "@/src/theme";
import { usesNativeTabs } from "@/src/navigation";
import { ChallengeBanner } from "@/src/rapid/ChallengeBanner";
import { useInbox } from "@/src/rapid/social";

const ITEMS: Record<string, { label: string; icon: IconName }> = {
  index: { label: "Home", icon: "home-variant-outline" },
  rank: { label: "Rank", icon: "podium" },
  rapid: { label: "Rapid Fire", icon: "lightning-bolt" },
  tests: { label: "My Tests", icon: "clipboard-text-outline" },
  mission: { label: "Mission", icon: "compass-outline" },
};
// The bar stays ink-black on every tab (light app, dark dock), like a premium wallet.
const BAR = colors.custom_dock, ON = colors.custom_dockInk, OFF = colors.custom_dockMuted;
const GEM = require("../../assets/images/rapid-gem.webp");
// Same diamond with a differently shaped flame; cross-fading the two makes the fire flicker.
const GEM_FLICKER = require("../../assets/images/rapid-gem-flicker.webp");

function RapidGem({ style }: { style: StyleProp<ViewStyle> }) {
  const reduced = useReducedMotion();
  const flame = useSharedValue(0);
  useEffect(() => {
    if (reduced) return;
    const step = (to: number, ms: number) => withTiming(to, { duration: ms, easing: Easing.inOut(Easing.quad) });
    flame.value = withRepeat(withSequence(step(0.9, 420), step(0.3, 300), step(0.75, 380), step(0, 520)), -1, false);
    return () => cancelAnimation(flame);
  }, [reduced, flame]);
  const flicker = useAnimatedStyle(() => ({ opacity: flame.value }));
  return (
    <View testID="tab-rapid-gem" style={style} accessible={false}>
      <Image source={GEM} resizeMode="contain" style={styles.gemLayer} />
      <Animated.Image source={GEM_FLICKER} resizeMode="contain" style={[styles.gemLayer, flicker]} />
    </View>
  );
}

function JeeTabBar({ state, emitter, navigateToTab }: any) {
  const insets = useSafeAreaInsets();
  const narrow = useWindowDimensions().width < 360;
  const labelSize = narrow ? 10 : 10.5;
  const challenged = !!useInbox()?.challenges.length;
  // Inside Rapid Fire the arena shows its own bar (Home, Trophy, Arena, Gang, Store).
  if (state.routes[state.index]?.name === "rapid") return null;
  return (
    <View style={[styles.bar, { paddingBottom: insets.bottom, height: (Platform.OS === "web" ? 70 : 68) + insets.bottom }]}>
      {state.routes.map((route: any, i: number) => {
        const item = ITEMS[route.name];
        if (!item) return null;
        const focused = state.index === i;
        const onPress = () => {
          const e = emitter?.emit?.({ type: "tabPress", target: route.key, canPreventDefault: true });
          if (!focused && !e?.defaultPrevented) navigateToTab(route.key);
        };
        if (route.name === "rapid") {
          return (
            <View key={route.key} style={styles.rapidCol}>
              <Press testID="tab-rapid" onPress={onPress} accessibilityLabel="Rapid Fire arena" accessibilityState={{ selected: focused }} style={styles.rapidPress} scaleTo={0.92}>
                {/* Sparkly blue diamond with a soft fire inside (transparent artwork) rising out of the dock. */}
                <RapidGem style={[styles.gem, narrow && styles.gemNarrow, focused && styles.gemOn]} />
                {challenged ? <View testID="tab-rapid-dot" accessibilityLabel="A challenge is waiting" style={styles.dot} /> : null}
                <T w="bold" size={labelSize} numberOfLines={1} color={focused ? ON : colors.custom_gemBlue} style={styles.label}>RAPID FIRE</T>
              </Press>
            </View>
          );
        }
        return (
          <Press key={route.key} testID={"tab-" + route.name} onPress={onPress} accessibilityLabel={item.label} accessibilityRole="tab" accessibilityState={{ selected: focused }} style={styles.item} scaleTo={0.94}>
            <Glyph name={item.icon} size={24} color={focused ? ON : OFF} stroke={focused ? 1.9 : 1.5} />
            <T w="bold" size={labelSize} numberOfLines={1} color={focused ? ON : OFF} style={styles.label}>{item.label.toUpperCase()}</T>
          </Press>
        );
      })}
    </View>
  );
}

export default function TabsLayout() {
  // A challenge can arrive while the student is on Home.
  const onHome = (useSegments() as string[]).length === 1;
  if (usesNativeTabs) {
    return (
      <NativeTabs tintColor={colors.brandPrimary}>
        <NativeTabs.Trigger name="index"><NativeTabs.Trigger.Icon sf="house.fill" /><NativeTabs.Trigger.Label>Home</NativeTabs.Trigger.Label></NativeTabs.Trigger>
        <NativeTabs.Trigger name="rank"><NativeTabs.Trigger.Icon sf="trophy.fill" /><NativeTabs.Trigger.Label>Rank</NativeTabs.Trigger.Label></NativeTabs.Trigger>
        <NativeTabs.Trigger name="rapid"><NativeTabs.Trigger.Icon sf="bolt.fill" /><NativeTabs.Trigger.Label>Rapid</NativeTabs.Trigger.Label></NativeTabs.Trigger>
        <NativeTabs.Trigger name="tests"><NativeTabs.Trigger.Icon sf="list.clipboard.fill" /><NativeTabs.Trigger.Label>Tests</NativeTabs.Trigger.Label></NativeTabs.Trigger>
        <NativeTabs.Trigger name="mission"><NativeTabs.Trigger.Icon sf="safari" /><NativeTabs.Trigger.Label>Mission</NativeTabs.Trigger.Label></NativeTabs.Trigger>
      </NativeTabs>
    );
  }
  return (
    <View style={styles.root}>
      <Tabs screenOptions={{ headerShown: false, sceneStyle: { backgroundColor: colors.surface } }} tabBar={(p) => <JeeTabBar {...p} />}>
        <Tabs.Screen name="index" />
        <Tabs.Screen name="rank" />
        <Tabs.Screen name="rapid" />
        <Tabs.Screen name="tests" />
        <Tabs.Screen name="mission" />
      </Tabs>
      {onHome ? <ChallengeBanner floating /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  dot: { position: "absolute", top: 0, right: 6, width: 12, height: 12, borderRadius: 6, backgroundColor: colors.brandPrimary, borderWidth: 2, borderColor: BAR },
  bar: { flexDirection: "row", overflow: "visible", backgroundColor: BAR, borderTopLeftRadius: 0, paddingTop: 2 },
  item: { flex: 1, minWidth: 0, alignItems: "center", justifyContent: "center", gap: 6, paddingTop: space.xs },
  label: { letterSpacing: 0.9 },
  rapidCol: { flex: 1.3, alignItems: "center" },
  rapidPress: { alignItems: "center", marginTop: -22, gap: 4 },
  // Artwork is 190×224 (royal-blue rhombus, 20% wider and 20% shorter than the first cut); keep that ratio.
  gem: { width: 48, height: 56 },
  gemNarrow: { width: 41, height: 48 },
  gemOn: { transform: [{ scale: 1.08 }] },
  // Explicit size: web otherwise gives a required image its natural 265×240 size.
  gemLayer: { position: "absolute", top: 0, left: 0, width: "100%", height: "100%" },
});
