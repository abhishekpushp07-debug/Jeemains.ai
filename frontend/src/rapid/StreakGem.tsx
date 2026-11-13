import React, { useEffect } from "react";
import { StyleSheet, View, useWindowDimensions } from "react-native";
import Animated, { Easing, ZoomIn, interpolate, runOnJS, useAnimatedStyle, useReducedMotion, useSharedValue, withTiming } from "react-native-reanimated";
import { T, buzz } from "@/src/components/ui";
import { playSfx } from "@/src/sfx";
import { arena, gemColors } from "@/src/theme";
import { Alive, GEM_AT, GEM_LABEL, GEM_ORDER, Gem, GemColor, PhoenixDiamond } from "./Art";
import { Panel } from "./arena";
import { Pop } from "./juice";

// Phoenix streak: correct answers in a row inside one match. 3 / 5 / 10 / 15 / 20 each light a diamond.
export const gemAt = (streak: number): GemColor | null => GEM_ORDER.find((c) => GEM_AT[c] === streak) || null;
export const trailingStreak = (answers?: { outcome: string }[]) => {
  let n = 0;
  for (let i = (answers?.length || 0) - 1; i >= 0 && answers![i].outcome === "correct"; i--) n++;
  return n;
};

/** Sits beside the score: unlit with a count (2/3) until a milestone, then burning in that diamond's colour. */
export function StreakGem({ streak }: { streak: number }) {
  const reduced = useReducedMotion();
  const lit = [...GEM_ORDER].reverse().find((c) => GEM_AT[c] <= streak);
  const next = GEM_ORDER.find((c) => GEM_AT[c] > streak);
  return <View testID="rf-streak-gem" accessibilityLabel={`Phoenix streak ${streak}`} style={[styles.chip, lit && { borderColor: gemColors[lit] }]}>
    <Animated.View key={lit || "off"} entering={reduced || !lit ? undefined : ZoomIn.springify().damping(7)}><Gem color={lit || next || "kohinoor"} size={30} dim={!lit} /></Animated.View>
    <T testID="rf-streak-count" w="heavy" size={13} color={lit ? arena.gold : arena.muted}>{next ? `${streak}/${GEM_AT[next]}` : `${streak} MAX`}</T>
  </View>;
}

/** A rival's live streak, shown next to their score once it lights a diamond (3 or more in a row). */
export function RivalGem({ streak, size = 18, testID }: { streak: number; size?: number; testID?: string }) {
  const lit = [...GEM_ORDER].reverse().find((c) => GEM_AT[c] <= streak);
  if (!lit) return null;
  return <View testID={testID} accessibilityLabel={`On a streak of ${streak}`} style={styles.rival}><Gem color={lit} size={size} /><T w="heavy" size={10} color={arena.gold}>{streak}</T></View>;
}

/** The moment a diamond is won, played in the gap between two cards. Bigger and brighter for rarer diamonds. */
export function GemFlare({ color, onDone }: { color: GemColor; onDone: () => void }) {
  const reduced = useReducedMotion();
  const tier = GEM_ORDER.indexOf(color);
  const t = useSharedValue(0);
  useEffect(() => {
    playSfx(tier >= 3 ? "levelup" : "combo");
    buzz("success");
    t.value = withTiming(1, { duration: 1000, easing: Easing.out(Easing.quad) }, (f) => { if (f) runOnJS(onDone)(); });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const wash = useAnimatedStyle(() => ({ opacity: reduced ? 0 : interpolate(t.value, [0, 0.12, 1], [0, 0.18 + tier * 0.11, 0]) }));
  // The answered card dims behind the diamond, so nothing fights with it.
  const dim = useAnimatedStyle(() => ({ opacity: interpolate(t.value, [0, 0.1, 0.8, 1], [0, 1, 1, 0]) }));
  const body = useAnimatedStyle(() => ({ opacity: interpolate(t.value, [0, 0.1, 0.8, 1], [0, 1, 1, 0]), transform: [{ scale: reduced ? 1 : interpolate(t.value, [0, 0.22, 0.36, 1], [0.3, 1.18, 1, 1.06]) }] }));
  const width = Math.min(useWindowDimensions().width - 24, 250 + tier * 45);
  return <View pointerEvents="none" testID="rf-gem-flare" style={[StyleSheet.absoluteFill, styles.flare]}>
    <Animated.View style={[StyleSheet.absoluteFill, styles.dim, dim]} />
    <Animated.View style={[StyleSheet.absoluteFill, { backgroundColor: gemColors[color] }, wash]} />
    <Animated.View style={[styles.center, body]}>
      {/* The Phoenix lights up in the colour just won and throws its wings open. */}
      <PhoenixDiamond width={width} color={color} burst />
      <T w="heavy" size={24} color={arena.gold} style={styles.shadow}>{GEM_LABEL[color].toUpperCase()} DIAMOND!</T>
      <T w="bold" size={13} color={arena.aqua}>{GEM_AT[color]} correct in a row</T>
    </Animated.View>
  </View>;
}

type Won = { diamonds?: Record<string, number>; phoenix_streak?: number } | null;
/** Result card: the diamonds won in this match, popping in one by one, and the longest streak. */
export function DiamondsWon({ reward, testID = "rf-diamonds-won" }: { reward?: Won; testID?: string }) {
  if (!reward) return null;
  const won = GEM_ORDER.filter((c) => reward.diamonds?.[c]);
  return <Panel gold={!!won.length} testID={testID} style={styles.won}>
    <T w="heavy" size={12} color={arena.gold} style={styles.spaced}>DIAMONDS WON</T>
    {won.length ? <View style={styles.wonRow}>{won.map((c, i) => <Pop key={c} delay={300 + i * 220} style={styles.center}>
      <Gem color={c} size={48} testID={`${testID}-${c}`} /><T w="heavy" size={14} color={arena.text}>×{reward.diamonds![c]}</T>
    </Pop>)}</View> : <T testID={`${testID}-none`} size={13} color={arena.muted} style={styles.centerText}>No diamonds this time. 3 correct in a row lights the Red diamond.</T>}
    <T testID={`${testID}-streak`} w="bold" size={12} color={arena.aqua}>Longest Phoenix streak: {reward.phoenix_streak ?? 0}</T>
  </Panel>;
}

const styles = StyleSheet.create({
  chip: { flexDirection: "row", alignItems: "center", gap: 4, height: 40, paddingLeft: 4, paddingRight: 10, borderRadius: 20, backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  rival: { flexDirection: "row", alignItems: "center", gap: 1 },
  flare: { zIndex: 45, alignItems: "center", justifyContent: "center" }, dim: { backgroundColor: arena.scrim }, center: { alignItems: "center", justifyContent: "center" },
  shadow: { letterSpacing: 2, textShadowColor: arena.bgDeep, textShadowOffset: { width: 0, height: 3 }, textShadowRadius: 2 },
  won: { padding: 16, gap: 10, alignItems: "center" }, wonRow: { flexDirection: "row", gap: 18, justifyContent: "center" }, spaced: { letterSpacing: 2 }, centerText: { textAlign: "center" },
});
