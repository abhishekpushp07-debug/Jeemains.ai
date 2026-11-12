import React from "react";
import { Platform, StyleSheet, View, useWindowDimensions } from "react-native";
import { Tabs } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { NativeTabs } from "expo-router/native-tabs";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { IconName, Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { colors, space } from "@/src/theme";
import { usesNativeTabs } from "@/src/navigation";

const ITEMS: Record<string, { label: string; icon: IconName }> = {
  index: { label: "Home", icon: "home-variant-outline" },
  rank: { label: "Rank", icon: "podium" },
  rapid: { label: "Rapid Fire", icon: "lightning-bolt" },
  tests: { label: "My Tests", icon: "clipboard-text-outline" },
  mission: { label: "Mission", icon: "compass-outline" },
};
// The bar stays ink-black on every tab (light app, dark dock), like a premium wallet.
const BAR = colors.custom_dock, ON = colors.custom_dockInk, OFF = colors.custom_dockMuted;

function JeeTabBar({ state, emitter, navigateToTab }: any) {
  const insets = useSafeAreaInsets();
  const narrow = useWindowDimensions().width < 360;
  const labelSize = narrow ? 10 : 10.5;
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
                {/* Royal-blue glass capsule: outer view carries the glow, inner view clips the layers. */}
                <View testID="tab-rapid-glass" style={[styles.glassGlow, focused && styles.glassGlowOn]}>
                  <View style={[styles.glass, narrow && styles.glassNarrow, focused && styles.glassOn]}>
                    <LinearGradient colors={[colors.custom_rfGlassFrom, colors.custom_rfGlassMid, colors.custom_rfGlassTo]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
                    <LinearGradient colors={[colors.custom_rfGlassSheen, colors.custom_clear]} start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }} style={styles.sheen} />
                    <View><Glyph name="lightning-bolt" size={narrow ? 22 : 24} color={colors.custom_rfGlassInk} stroke={1.9} /></View>
                  </View>
                </View>
                <T w="bold" size={labelSize} numberOfLines={1} color={focused ? ON : colors.custom_rfGlassLine} style={styles.label}>RAPID FIRE</T>
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
    <Tabs screenOptions={{ headerShown: false, sceneStyle: { backgroundColor: colors.surface } }} tabBar={(p) => <JeeTabBar {...p} />}>
      <Tabs.Screen name="index" />
      <Tabs.Screen name="rank" />
      <Tabs.Screen name="rapid" />
      <Tabs.Screen name="tests" />
      <Tabs.Screen name="mission" />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  bar: { flexDirection: "row", overflow: "visible", backgroundColor: BAR, borderTopLeftRadius: 0, paddingTop: 2 },
  item: { flex: 1, minWidth: 0, alignItems: "center", justifyContent: "center", gap: 6, paddingTop: space.xs },
  label: { letterSpacing: 0.9 },
  rapidCol: { flex: 1.3, alignItems: "center" },
  rapidPress: { alignItems: "center", marginTop: -22, gap: 6 },
  glassGlow: { borderRadius: 28, backgroundColor: colors.custom_rfGlassMid, shadowColor: colors.custom_rfGlassGlow, shadowOpacity: 0.55, shadowRadius: 16, shadowOffset: { width: 0, height: 6 }, elevation: 12 },
  glassGlowOn: { shadowOpacity: 0.85, shadowRadius: 22 },
  glass: { width: 80, height: 54, borderRadius: 27, overflow: "hidden", borderWidth: 2, borderColor: colors.custom_rfGlassLine, alignItems: "center", justifyContent: "center" },
  glassNarrow: { width: 68, height: 50, borderRadius: 25 },
  glassOn: { borderColor: colors.custom_dockInk },
  sheen: { position: "absolute", top: 0, left: 0, right: 0, height: "55%" },
});
