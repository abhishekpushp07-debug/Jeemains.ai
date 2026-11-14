import React, { useEffect } from "react";
import { Modal, Platform, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import Animated, { Easing, Extrapolation, cancelAnimation, interpolate, useAnimatedStyle, useReducedMotion, useSharedValue, withDelay, withRepeat, withSpring, withTiming } from "react-native-reanimated";
import Svg, { Circle, Defs, Ellipse, G, LinearGradient as Grad, Path, RadialGradient, Rect, Stop } from "react-native-svg";
import { T } from "@/src/components/ui";
import { playSfx } from "@/src/sfx";
import { arena, fx, gemColors } from "@/src/theme";
import { GoldTitle, RaisedButton } from "./arena";
import { Confetti, Pop, Twinkles } from "./juice";
import { Crown } from "./parts";

/** A jewelled royal crown, gold or silver, drawn so it stays sharp at any size. */
export function CrownArt({ size, gold }: { size: number; gold: boolean }) {
  const [hi, mid, low] = gold ? [fx.white, arena.gold, arena.goldDeep] : [fx.white, fx.smoke, arena.faint];
  return <Svg width={size} height={size * 0.8} viewBox="0 0 220 176">
    <Defs>
      <Grad id="metal" x1="0" y1="0" x2="0" y2="1"><Stop offset="0" stopColor={hi} /><Stop offset="0.35" stopColor={mid} /><Stop offset="1" stopColor={low} /></Grad>
      <Grad id="band" x1="0" y1="0" x2="0" y2="1"><Stop offset="0" stopColor={mid} /><Stop offset="1" stopColor={low} /></Grad>
      <RadialGradient id="ruby" cx="0.35" cy="0.35" r="0.7"><Stop offset="0" stopColor={fx.white} /><Stop offset="0.3" stopColor={gemColors.red} /><Stop offset="1" stopColor={arena.bgDeep} /></RadialGradient>
      <RadialGradient id="sapph" cx="0.35" cy="0.35" r="0.7"><Stop offset="0" stopColor={fx.white} /><Stop offset="0.3" stopColor={gemColors.blue} /><Stop offset="1" stopColor={fx.night} /></RadialGradient>
      <RadialGradient id="emer" cx="0.35" cy="0.35" r="0.7"><Stop offset="0" stopColor={fx.white} /><Stop offset="0.3" stopColor={gemColors.emerald} /><Stop offset="1" stopColor={arena.tealOutline} /></RadialGradient>
      <RadialGradient id="pearl" cx="0.35" cy="0.3" r="0.7"><Stop offset="0" stopColor={fx.white} /><Stop offset="1" stopColor={low} /></RadialGradient>
    </Defs>
    {/* the five points and the body */}
    <Path d="M30 132 L14 50 L66 96 L82 40 L110 88 L138 40 L154 96 L206 50 L190 132 Z" fill="url(#metal)" stroke={arena.badgeInk} strokeWidth={4} strokeLinejoin="round" />
    <Path d="M40 124 L30 70 L68 104 L84 60 L110 100 L136 60 L152 104 L190 70 L182 124 Z" fill={hi} opacity={0.18} />
    {/* pearls on every point */}
    {[[14, 50, 10], [82, 40, 9], [110, 22, 13], [138, 40, 9], [206, 50, 10]].map(([x, y, r]) => <Circle key={x} cx={x} cy={y} r={r} fill="url(#pearl)" stroke={arena.badgeInk} strokeWidth={3} />)}
    <Path d="M110 34 L110 86" stroke={arena.badgeInk} strokeWidth={4} />
    {/* the band, studded with jewels */}
    <Rect x={24} y={128} width={172} height={36} rx={10} fill="url(#band)" stroke={arena.badgeInk} strokeWidth={4} />
    <Rect x={32} y={133} width={156} height={7} rx={3.5} fill={hi} opacity={0.45} />
    <G stroke={arena.badgeInk} strokeWidth={3}>
      <Ellipse cx={110} cy={146} rx={16} ry={12} fill="url(#ruby)" />
      <Ellipse cx={66} cy={146} rx={11} ry={9} fill="url(#sapph)" />
      <Ellipse cx={154} cy={146} rx={11} ry={9} fill="url(#sapph)" />
      <Circle cx={38} cy={146} r={6} fill="url(#emer)" />
      <Circle cx={182} cy={146} r={6} fill="url(#emer)" />
      <Ellipse cx={110} cy={108} rx={12} ry={14} fill="url(#ruby)" />
      <Circle cx={60} cy={116} r={7} fill="url(#emer)" />
      <Circle cx={160} cy={116} r={7} fill="url(#emer)" />
    </G>
  </Svg>;
}

/** Golden rays that slowly turn behind the crown. */
function Rays({ size, color }: { size: number; color: string }) {
  const r = size / 2;
  return <Svg width={size} height={size} viewBox={`${-r} ${-r} ${size} ${size}`}>
    <Defs><RadialGradient id="halo" cx="0" cy="0" r={r * 0.5} gradientUnits="userSpaceOnUse"><Stop offset="0" stopColor={color} stopOpacity={0.8} /><Stop offset="1" stopColor={color} stopOpacity={0} /></RadialGradient></Defs>
    {Array.from({ length: 16 }, (_, i) => <Path key={i} d={`M0 0 L${-r * 0.1} ${-r} L${r * 0.1} ${-r} Z`} fill={color} opacity={i % 2 ? 0.12 : 0.26} transform={`rotate(${i * 22.5})`} />)}
    <Circle r={r * 0.5} fill="url(#halo)" />
  </Svg>;
}

type CrownCount = { won: number; real: number };

/** What the celebration says: the first crown is special, every crown after it adds to the count. */
function words(no: number, gold: boolean, crown: CrownCount) {
  if (no <= 1) return { kicker: "FIRST CROWN", title: "You are a Cup Champion!",
    line: gold ? "You beat real players. Your gold crown now shines next to your name everywhere." : "Your silver crown now sits next to your name. Win a cup against real players to turn it gold." };
  return { kicker: `CROWN #${no}`, title: "Champion again!",
    line: gold ? `Cup number ${no} is yours, won against real players. Your crown count just went up.` : crown.real ? `Cup number ${no} is yours. Your gold crown shows every title you win.` : `Cup number ${no} is yours. Win one against real players to turn your crown gold.` };
}

/**
 * Every Knockout Cup a player wins: the crown drops from the sky onto a turning sunburst, confetti rains, and the
 * player sees their crown count grow. Gold rays when real players were beaten, silver when the cup was against
 * practice rivals. Scrolls on short phones so the buttons are always reachable.
 */
export function CrownCelebration({ visible, gold: realCup, no = 1, crown, onSee, onClose }: { visible: boolean; gold: boolean; no?: number; crown?: CrownCount | null; onSee: () => void; onClose: () => void }) {
  const { width: W, height: H } = useWindowDimensions();
  const total: CrownCount = crown?.won ? crown : { won: no, real: realCup ? 1 : 0 };
  const say = words(no, realCup, total);
  const gold = total.real > 0; // the art shines in the colour of your crown, like the chip under it
  const reduced = !!useReducedMotion();
  const drop = useSharedValue(0), spin = useSharedValue(0), glow = useSharedValue(0);
  useEffect(() => {
    if (!visible) return;
    drop.value = 0;
    drop.value = withDelay(250, withSpring(1, { damping: 7, stiffness: 85, mass: 0.9 }));
    spin.value = withRepeat(withTiming(360, { duration: 16000, easing: Easing.linear }), -1, false);
    glow.value = withRepeat(withTiming(1, { duration: 1300, easing: Easing.inOut(Easing.quad) }), -1, true);
    playSfx("levelup");
    const t = setTimeout(() => { playSfx("win", 0.9); if (Platform.OS !== "web") Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {}); }, 750);
    return () => { clearTimeout(t); cancelAnimation(spin); cancelAnimation(glow); };
  }, [visible]); // eslint-disable-line react-hooks/exhaustive-deps

  const size = Math.min(W * 0.66, 300, H * 0.3), raySize = Math.min(Math.max(W, H) * 0.95, 760), stage = Math.min(300, H * 0.36);
  const drop3d = useAnimatedStyle(() => ({
    opacity: interpolate(drop.value, [0, 0.15], [0, 1], Extrapolation.CLAMP),
    transform: reduced ? [] : [{ translateY: interpolate(drop.value, [0, 1], [-H * 0.55, 0]) }, { rotate: `${interpolate(drop.value, [0, 1], [-28, 0])}deg` }, { scale: interpolate(drop.value, [0, 1], [0.55, 1]) }],
  }));
  const rays = useAnimatedStyle(() => ({ opacity: interpolate(drop.value, [0.6, 1], [0, 1], Extrapolation.CLAMP), transform: [{ rotate: `${reduced ? 0 : spin.value}deg` }, { scale: reduced ? 1 : 0.94 + glow.value * 0.1 }] }));
  const shine = useAnimatedStyle(() => ({ opacity: reduced ? 0.5 : 0.25 + glow.value * 0.45 }));

  return <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose} statusBarTranslucent>
    <View testID="crown-celebration" style={styles.flex}>
      <LinearGradient pointerEvents="none" colors={[arena.scrim, arena.bgDeep, arena.scrim]} style={StyleSheet.absoluteFill} />
      <ScrollView style={styles.flex} contentContainerStyle={styles.root} showsVerticalScrollIndicator={false} bounces={false}>
      <View style={[styles.stage, { minHeight: stage }]}>
        <Animated.View pointerEvents="none" style={[styles.rays, rays]}><Rays size={raySize} color={gold ? arena.gold : fx.white} /></Animated.View>
        <Animated.View pointerEvents="none" style={[styles.shine, { width: size * 1.2, height: size * 1.2, borderRadius: size * 0.6, backgroundColor: gold ? arena.goldSoft : arena.gloss }, shine]} />
        <Animated.View style={drop3d} testID="crown-celebration-crown"><CrownArt size={size} gold={gold} /></Animated.View>
        <Twinkles spots={[[16, 20, 18], [82, 14, 14], [10, 64, 12], [88, 58, 16], [50, 4, 12], [30, 86, 10], [72, 90, 12]]} color={gold ? arena.gold : fx.white} />
      </View>
      <View style={styles.copy}>
        <Pop delay={700}><T testID="crown-celebration-kicker" w="heavy" size={13} color={arena.aqua} style={styles.kicker}>{say.kicker}</T></Pop>
        <Pop delay={820}><GoldTitle size={H < 640 ? 26 : 32} center testID="crown-celebration-title">{say.title}</GoldTitle></Pop>
        <Pop delay={940}>
          <View testID="crown-celebration-chip" style={styles.chipRow}><Crown c={total} size="lg" />
            <T w="heavy" size={13} color={total.real ? arena.gold : fx.smoke}>{total.real ? "GOLD CROWN" : "SILVER CROWN"} · {total.won} CUP{total.won === 1 ? "" : "S"}</T></View>
        </Pop>
        <Pop delay={1040}><T testID="crown-celebration-line" w="bold" size={14} color={arena.text} style={styles.center}>{say.line}</T></Pop>
        <View style={styles.buttons}>
          <RaisedButton testID="crown-celebration-see" icon="trophy" height={60} streak label="SEE MY CROWN" sub="On your profile" onPress={onSee} />
          <RaisedButton testID="crown-celebration-close" tone="wine" label="Continue" onPress={onClose} />
        </View>
      </View>
      </ScrollView>
      <Confetti count={64} />
    </View>
  </Modal>;
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  root: { flexGrow: 1, justifyContent: "center", paddingHorizontal: 20, paddingVertical: 32, gap: 8 },
  stage: { alignItems: "center", justifyContent: "center" },
  rays: { position: "absolute" }, shine: { position: "absolute" },
  copy: { alignItems: "center", gap: 10, width: "100%", maxWidth: 460, alignSelf: "center" },
  kicker: { letterSpacing: 3 }, center: { textAlign: "center" },
  chipRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  buttons: { alignSelf: "stretch", gap: 10, marginTop: 6 },
});
