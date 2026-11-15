import React, { useEffect } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { useAnimatedStyle, useReducedMotion, useSharedValue, withSequence, withSpring, withTiming } from "react-native-reanimated";
import { LinearGradient } from "expo-linear-gradient";
import { T } from "@/src/components/ui";
import { useAuth } from "@/src/auth";
import { rewardsReady, useGameProfile } from "@/src/components/game";
import { arena } from "@/src/theme";
import { ARENA } from "@/src/arenaMode";
import { websiteHomeUrl } from "@/src/api/client";
import { GameIcon, GameIconName, GemColor, PhoenixDiamond, topGem } from "./Art";
import { Badge } from "./arena";
import { Jelly, Twinkles } from "./juice";
import { ArenaTab, gangNotices, setArenaTab, useArenaTab, useInbox } from "./social";

type Key = "home" | ArenaTab;
const ITEMS: { key: Key; label: string; icon?: GameIconName }[] = [
  { key: "home", label: "Home", icon: "home" }, { key: "trophy", label: "Trophy", icon: "trophy" }, { key: "arena", label: "Arena" },
  { key: "gang", label: "Gang", icon: "gang" }, { key: "store", label: "Store", icon: "store" },
];

function Item({ item, on, badge, onPress }: { item: (typeof ITEMS)[number]; on: boolean; badge: number; onPress: () => void }) {
  const reduced = useReducedMotion();
  const lift = useSharedValue(on ? 1 : 0);
  useEffect(() => {
    // The chosen icon jumps up, overshoots and settles; the others drop back.
    lift.value = reduced ? (on ? 1 : 0) : on ? withSequence(withTiming(1.6, { duration: 110 }), withSpring(1, { damping: 5, stiffness: 240 })) : withTiming(0, { duration: 160 });
  }, [on, reduced, lift]);
  const a = useAnimatedStyle(() => ({ transform: [{ translateY: -5 * lift.value }, { scale: 1 + 0.16 * lift.value }, { rotate: `${Math.max(0, lift.value - 1) * -18}deg` }] }));
  const centre = item.key === "arena";
  return <Jelly testID={`arena-tab-${item.key}`} onPress={onPress} accessibilityRole="tab" accessibilityLabel={item.label} accessibilityState={{ selected: on }} style={centre ? styles.centre : styles.item}>
    {centre ? <View style={styles.diamond}>
      <LinearGradient colors={[arena.rimHi, arena.panelHi, arena.bar]} style={styles.plate} />
      <Animated.View style={a}><PhoenixDiamond width={92} breathe={on} testID="arena-tab-phoenix" /></Animated.View>
      {on ? <Twinkles spots={[[12, 22, 12], [88, 30, 10], [50, 4, 9]]} /> : null}
    </View> : <Animated.View style={a}><GameIcon name={item.icon!} size={40} /></Animated.View>}
    {badge ? <Badge n={badge > 9 ? "9+" : badge} testID={`arena-tab-${item.key}-badge`} style={styles.badge} /> : null}
    <T w="heavy" size={10.5} color={on ? arena.gold : arena.muted} style={styles.label}>{item.label.toUpperCase()}</T>
  </Jelly>;
}

/** The arena's own bottom bar: Home, Trophy, Arena (raised Phoenix Diamond), Gang, Store. */
export function ArenaBar() {
  const insets = useSafeAreaInsets(), router = useRouter(), tab = useArenaTab(), inbox = useInbox();
  const profile = useGameProfile(useAuth().user?.id).data;
  const badges: Partial<Record<Key, number>> = {
    trophy: rewardsReady(profile),
    gang: (inbox?.challenges.length || 0) + gangNotices(inbox).length,
  };
  return <View testID="arena-bar" style={[styles.bar, { paddingBottom: insets.bottom, height: 66 + insets.bottom }]}>
    <LinearGradient pointerEvents="none" colors={[arena.clear, arena.gold, arena.clear]} start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }} style={styles.line} />
    {ITEMS.map((item) => <Item key={item.key} item={item} on={item.key === tab} badge={badges[item.key] || 0}
      onPress={() => (item.key !== "home" ? setArenaTab(item.key) : ARENA ? window.location.assign(websiteHomeUrl()) : router.navigate("/(tabs)"))} />)}
  </View>;
}

const styles = StyleSheet.create({
  bar: { flexDirection: "row", backgroundColor: arena.bar, borderTopWidth: 1.5, borderTopColor: arena.rim, overflow: "visible" },
  line: { position: "absolute", top: -1.5, left: 0, right: 0, height: 1.5, opacity: 0.6 },
  item: { flex: 1, minHeight: 56, alignItems: "center", justifyContent: "flex-end", paddingBottom: 6, gap: 1 },
  centre: { flex: 1.25, alignItems: "center", justifyContent: "flex-end", paddingBottom: 6, gap: 1 },
  diamond: { width: 96, height: 64, marginTop: -16, alignItems: "center", justifyContent: "center" },
  plate: { position: "absolute", width: 70, height: 70, borderRadius: 35, borderWidth: 2, borderColor: arena.rim },
  badge: { position: "absolute", top: 0, right: "16%" }, label: { letterSpacing: 0.8 },
});
