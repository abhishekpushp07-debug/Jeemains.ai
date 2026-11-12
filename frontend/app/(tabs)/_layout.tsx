import React from "react";
import { Platform, StyleSheet, View } from "react-native";
import { Tabs } from "expo-router";
import { NativeTabs } from "expo-router/native-tabs";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { Icon, IconName, Press, T } from "@/src/components/ui";
import { colors, rapidColors, space } from "@/src/theme";
import { usesNativeTabs } from "@/src/navigation";

const ITEMS: Record<string, { label: string; icon: IconName; active: IconName }> = {
  index: { label: "Home", icon: "home-variant-outline", active: "home-variant" },
  jee: { label: "JEE Main", icon: "atom-variant", active: "atom-variant" },
  rapid: { label: "Rapid Fire", icon: "diamond-stone", active: "diamond-stone" },
  tests: { label: "My Tests", icon: "clipboard-text-outline", active: "clipboard-text" },
  mission: { label: "Mission", icon: "rocket-launch-outline", active: "rocket-launch" },
};

function JeeTabBar({ state, emitter, navigateToTab }: any) {
  const insets = useSafeAreaInsets();
  const gameActive = state.routes[state.index]?.name === "rapid";
  return (
    <View style={[styles.bar, { backgroundColor: gameActive ? rapidColors.surface : colors.custom_bar, borderTopColor: gameActive ? rapidColors.border : colors.custom_barLine, paddingBottom: insets.bottom, height: (Platform.OS === "web" ? 68 : 66) + insets.bottom }]}>
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
                <View style={styles.diamondBox}>
                  <View pointerEvents="none" style={[styles.glow, { backgroundColor: focused ? rapidColors.brandPrimary : colors.brandPrimary }]} />
                  <LinearGradient colors={focused ? [rapidColors.brandPrimary, rapidColors.custom_neonViolet] : [colors.custom_diamondFrom, colors.custom_diamondTo]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                    style={[styles.diamond, { borderColor: focused ? rapidColors.custom_neonCyan : colors.brandLine }]} />
                  <Icon name="lightning-bolt" size={24} color={colors.custom_webWhite} />
                </View>
                <T w="heavy" size={9} numberOfLines={1} color={focused ? rapidColors.custom_neonCyan : colors.custom_dim} style={styles.label}>RAPID FIRE</T>
              </Press>
            </View>
          );
        }
        return (
          <Press key={route.key} testID={"tab-" + route.name} onPress={onPress} accessibilityLabel={item.label} accessibilityRole="tab" accessibilityState={{ selected: focused }} style={styles.item}>
            <View style={[styles.iconWrap, focused && { backgroundColor: colors.custom_webGlass }]}>
              <Icon name={focused ? item.active : item.icon} size={22} color={focused ? colors.onSurface : colors.custom_dim} />
            </View>
            <T w="heavy" size={9} numberOfLines={1} color={focused ? colors.onSurface : colors.custom_dim} style={styles.label}>{item.label.toUpperCase()}</T>
          </Press>
        );
      })}
    </View>
  );
}

export default function TabsLayout() {
  if (usesNativeTabs) {
    return (
      <NativeTabs tintColor={colors.brandText}>
        <NativeTabs.Trigger name="index"><NativeTabs.Trigger.Icon sf="house.fill" /><NativeTabs.Trigger.Label>Home</NativeTabs.Trigger.Label></NativeTabs.Trigger>
        <NativeTabs.Trigger name="jee"><NativeTabs.Trigger.Icon sf="atom" /><NativeTabs.Trigger.Label>JEE</NativeTabs.Trigger.Label></NativeTabs.Trigger>
        <NativeTabs.Trigger name="rapid"><NativeTabs.Trigger.Icon sf="diamond.fill" /><NativeTabs.Trigger.Label>Rapid</NativeTabs.Trigger.Label></NativeTabs.Trigger>
        <NativeTabs.Trigger name="tests"><NativeTabs.Trigger.Icon sf="list.clipboard.fill" /><NativeTabs.Trigger.Label>Tests</NativeTabs.Trigger.Label></NativeTabs.Trigger>
        <NativeTabs.Trigger name="mission"><NativeTabs.Trigger.Icon sf="sparkles" /><NativeTabs.Trigger.Label>Mission</NativeTabs.Trigger.Label></NativeTabs.Trigger>
      </NativeTabs>
    );
  }
  return (
    <Tabs screenOptions={{ headerShown: false, sceneStyle: { backgroundColor: colors.surface } }} tabBar={(p) => <JeeTabBar {...p} />}>
      <Tabs.Screen name="index" />
      <Tabs.Screen name="jee" />
      <Tabs.Screen name="rapid" />
      <Tabs.Screen name="tests" />
      <Tabs.Screen name="mission" />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  bar: { borderTopWidth: 1, flexDirection: "row", overflow: "visible" },
  item: { flex: 1, minWidth: 0, alignItems: "center", justifyContent: "center", gap: 3, paddingTop: space.xs },
  iconWrap: { width: 44, height: 32, borderRadius: 16, alignItems: "center", justifyContent: "center" },
  label: { letterSpacing: 1.1 },
  rapidCol: { flex: 1.25, alignItems: "center" },
  rapidPress: { alignItems: "center", marginTop: -24, gap: 2 },
  diamondBox: { width: 64, height: 64, alignItems: "center", justifyContent: "center" },
  glow: { position: "absolute", width: 72, height: 72, borderRadius: 36, opacity: 0.16 },
  diamond: { position: "absolute", width: 44, height: 44, borderRadius: 11, transform: [{ rotate: "45deg" }], borderWidth: 1.5, shadowColor: colors.brandPrimary, shadowOpacity: 0.45, shadowRadius: 12, shadowOffset: { width: 0, height: 6 }, elevation: 8 },
});
