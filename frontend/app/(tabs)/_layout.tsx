import React from "react";
import { Image, Platform, StyleSheet, View, useWindowDimensions } from "react-native";
import { Tabs } from "expo-router";
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
const GEM = require("../../assets/images/rapid-gem.webp");

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
                {/* Winged ruby diamond (transparent artwork) rising out of the dock. */}
                <Image testID="tab-rapid-gem" source={GEM} resizeMode="contain" accessible={false}
                  style={[styles.gem, narrow && styles.gemNarrow, focused && styles.gemOn]} />
                <T w="bold" size={labelSize} numberOfLines={1} color={focused ? ON : colors.custom_seriesBright} style={styles.label}>RAPID FIRE</T>
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
  rapidPress: { alignItems: "center", marginTop: -26, gap: 4 },
  // Artwork is 360×201; keep that ratio so the wings never crop.
  gem: { width: 100, height: 56 },
  gemNarrow: { width: 82, height: 46 },
  gemOn: { transform: [{ scale: 1.08 }] },
});
