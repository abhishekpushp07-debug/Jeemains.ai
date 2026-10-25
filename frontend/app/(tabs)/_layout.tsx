import React from "react";
import { Platform, View } from "react-native";
import { Tabs } from "expo-router";
import { NativeTabs } from "expo-router/native-tabs";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { Icon, IconName, Press, T } from "@/src/components/ui";
import { colors, space } from "@/src/theme";
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
  return (
    <View style={{ backgroundColor: colors.surfaceSecondary, borderTopWidth: 1, borderTopColor: colors.border, paddingBottom: insets.bottom, flexDirection: "row", height: (Platform.OS === "web" ? 64 : 62) + insets.bottom, overflow: "visible" }}>
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
            <View key={route.key} style={{ flex: 1, alignItems: "center" }}>
              <Press testID="tab-rapid" onPress={onPress} accessibilityLabel="Rapid Fire arena" style={{ alignItems: "center", marginTop: -26 }} scaleTo={0.92}>
                <View style={{ width: 62, height: 62, alignItems: "center", justifyContent: "center" }}>
                  <LinearGradient colors={focused ? [colors.custom_seriesBright, colors.custom_series] : [colors.custom_series, colors.custom_seriesBright]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                    style={{ position: "absolute", width: 50, height: 50, borderRadius: 12, transform: [{ rotate: "45deg" }], borderWidth: 3, borderColor: colors.surfaceSecondary, shadowColor: colors.custom_series, shadowOpacity: 0.4, shadowRadius: 10, shadowOffset: { width: 0, height: 6 }, elevation: 8 }} />
                  <Icon name="diamond-stone" size={26} color={colors.onBrandSecondary} />
                </View>
                <T w="heavy" size={11} color={focused ? colors.custom_neonAmber : colors.muted} style={{ marginTop: 2, letterSpacing: 1 }}>RAPID</T>
              </Press>
            </View>
          );
        }
        const tint = focused ? colors.custom_seriesBright : colors.muted;
        return (
          <Press key={route.key} testID={"tab-" + route.name} onPress={onPress} accessibilityLabel={item.label} style={{ flex: 1, alignItems: "center", justifyContent: "center", gap: 2, paddingTop: space.xs }}>
            <View style={{ paddingHorizontal: 14, paddingVertical: 3, borderRadius: 14, backgroundColor: focused ? colors.custom_infoSoft : "transparent" }}>
              <Icon name={focused ? item.active : item.icon} size={23} color={route.name === "jee" && focused ? colors.custom_examJee : tint} />
            </View>
            <T w={focused ? "heavy" : "semibold"} size={11} color={focused ? colors.onSurface : colors.muted} numberOfLines={1}>{item.label}</T>
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
