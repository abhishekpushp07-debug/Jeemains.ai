import React, { useEffect, useState } from "react";
import { Modal, Platform, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import * as Haptics from "expo-haptics";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import Animated, { Easing, SharedValue, cancelAnimation, useAnimatedStyle, useReducedMotion, useSharedValue, withDelay, withRepeat, withTiming } from "react-native-reanimated";
import Svg, { Circle, Defs, Line, LinearGradient as Grad, Path, Stop } from "react-native-svg";
import { T } from "@/src/components/ui";
import { Avatar } from "@/src/components/Entry";
import { playSfx } from "@/src/sfx";
import { arena, fx, gemColors } from "@/src/theme";
import { RaisedButton } from "./arena";
import { CheerBanner, Pole } from "./CheerBanner";
import { Confetti, Pop, Twinkles } from "./juice";
import { CrownArt } from "./CrownArt";
import { SQUAD_GEO, squadFrames } from "./squadArt";

const ARENA = require("../../assets/arena/bg_colosseum.webp");
const COUNT = 8, BEAT = 430; // an 8-count routine
// One pose per count. Holders: 0 stand, 1 side kick, 2 knee lift, 3 lunge. Lead: 0 star jump, 1 high kick, 2 hip sway, 3 high-low.
const HOLD_SEQ = [0, 2, 0, 1, 0, 3, 2, 1];
const HOLD_HOP = [0.06, 0.03, 0.06, 0.02, 0.06, 0, 0.03, 0.02];
const LEAD_SEQ = [2, 0, 3, 1, 2, 0, 3, 1];
const LEAD_HOP = [0.02, 0.16, 0, 0.05, 0.02, 0.16, 0, 0.05];
const LEAD_SPIN = [0, 0, 1, 0, 0, 0, 1, 0]; // a full turn on counts 3 and 7
const GEMS = [gemColors.red, gemColors.gold, gemColors.emerald, gemColors.blue, gemColors.kohinoor];
// What each squad level brings to the stage (the banner's own colours are theme `cheer`).
const LOOK = {
  1: { beams: [arena.gold, arena.gold], bursts: 2, tint: null },
  2: { beams: [arena.gold, fx.ember], bursts: 4, tint: arena.goldSoft },
  3: { beams: [gemColors.blue, gemColors.kohinoor, fx.ice, gemColors.blue], bursts: 5, tint: `${gemColors.blue}2E` },
  4: { beams: GEMS.slice(0, 4), bursts: 7, tint: `${gemColors.kohinoor}24` },
} as const;
type Level = keyof typeof LOOK;

/** One pose of a dancer: shown only on the counts that use it. `clock` runs 0 → 1 over the whole of `seq` (one pose per count). */
function Frame({ src, i, clock, seq }: { src: number | { uri: string }; i: number; clock: SharedValue<number>; seq: number[] }) {
  const style = useAnimatedStyle(() => ({ opacity: seq[Math.floor(clock.value * seq.length) % seq.length] === i ? 1 : 0 }));
  return <Animated.View style={[StyleSheet.absoluteFill, style]}><Image source={src} style={StyleSheet.absoluteFill} contentFit="contain" transition={0} /></Animated.View>;
}

/** A dancer running the routine: the pose of each count, a hop, a squash on landing, a sway, and (lead only) full turns. */
export function Dancer({ frames, height, aspect, clock, seq, hops, spins, flip, style, testID }: {
  frames: (number | { uri: string })[]; height: number; aspect: number; clock: SharedValue<number>; seq: number[]; hops: number[]; spins?: number[]; flip?: boolean; style?: object; testID?: string;
}) {
  const w = height * aspect, dir = flip ? -1 : 1;
  const body = useAnimatedStyle(() => {
    const x = clock.value * seq.length, n = Math.floor(x) % seq.length, k = x - Math.floor(x);
    const turn = spins && spins[n] ? Math.cos(k * Math.PI * 2) : 1;
    return { transform: [{ translateY: -Math.sin(k * Math.PI) * hops[n] * height }, { rotate: `${Math.sin(k * Math.PI) * 3 * dir * (n % 2 ? 1 : -1)}deg` },
      { scaleX: dir * (Math.abs(turn) < 0.08 ? 0.08 * Math.sign(turn || 1) : turn) }, { scaleY: 1 - (1 - Math.min(1, k * 6)) * 0.035 }] };
  });
  const shadow = useAnimatedStyle(() => {
    const x = clock.value * seq.length, n = Math.floor(x) % seq.length, up = Math.sin((x - Math.floor(x)) * Math.PI) * hops[n] * 6;
    return { opacity: 0.32 - up * 0.2, transform: [{ scaleX: 1 - up * 0.4 }] };
  });
  return <View testID={testID} style={[{ position: "absolute", width: w, height }, style]}>
    <Animated.View style={[styles.shadow, { width: w * 0.4, left: w * 0.3, height: height * 0.035, borderRadius: w }, shadow]} />
    <Animated.View style={[StyleSheet.absoluteFill, body]}>{frames.map((f, i) => <Frame key={i} src={f} i={i} clock={clock} seq={seq} />)}</Animated.View>
  </View>;
}

/** A firework bursting in the sky over and over. */
export function Burst({ x, y, size, color, delay, testID }: { x: number; y: number; size: number; color: string; delay: number; testID?: string }) {
  const reduced = !!useReducedMotion();
  const p = useSharedValue(0);
  useEffect(() => {
    if (reduced) return;
    p.value = withDelay(delay, withRepeat(withTiming(1, { duration: 1500, easing: Easing.out(Easing.cubic) }), -1, false));
    return () => cancelAnimation(p);
  }, [reduced, delay]); // eslint-disable-line react-hooks/exhaustive-deps
  const style = useAnimatedStyle(() => ({ opacity: p.value < 0.08 ? p.value * 12 : Math.max(0, 1 - (p.value - 0.08) / 0.8), transform: [{ scale: 0.15 + p.value * 0.95 }] }));
  const rays = Array.from({ length: 14 }, (_, i) => (i / 14) * Math.PI * 2), c = size / 2;
  return <Animated.View testID={testID} pointerEvents="none" style={[{ position: "absolute", left: x - c, top: y - c, width: size, height: size }, style]}>
    <Svg width={size} height={size}>
      {rays.map((a) => <Line key={a} x1={c + Math.cos(a) * c * 0.22} y1={c + Math.sin(a) * c * 0.22} x2={c + Math.cos(a) * c * 0.86} y2={c + Math.sin(a) * c * 0.86} stroke={color} strokeWidth={2.4} strokeLinecap="round" />)}
      {rays.map((a) => <Circle key={`d${a}`} cx={c + Math.cos(a) * c * 0.95} cy={c + Math.sin(a) * c * 0.95} r={2.6} fill={fx.white} />)}
      <Circle cx={c} cy={c} r={c * 0.12} fill={fx.white} opacity={0.9} />
    </Svg>
  </Animated.View>;
}

/** A sweeping stage light from the top: a soft cone that fades towards the floor. */
export function Beam({ x, color, clock, height, phase }: { x: number; color: string; clock: SharedValue<number>; height: number; phase: number }) {
  const style = useAnimatedStyle(() => ({ transform: [{ rotate: `${Math.sin((clock.value + phase) * Math.PI * 2) * 26}deg` }] }));
  const id = `cone${Math.round(phase * 100)}`;
  return <Animated.View pointerEvents="none" style={[styles.beam, { height, left: x - BEAM_W / 2, transformOrigin: "top center" }, style]}>
    <Svg width={BEAM_W} height={height}>
      <Defs><Grad id={id} x1="0" y1="0" x2="0" y2="1"><Stop offset="0" stopColor={color} stopOpacity={0.5} /><Stop offset="0.6" stopColor={color} stopOpacity={0.12} /><Stop offset="1" stopColor={color} stopOpacity={0} /></Grad></Defs>
      <Path d={`M${BEAM_W / 2 - 10} 0 L${BEAM_W / 2 + 10} 0 L${BEAM_W} ${height} L0 ${height} Z`} fill={`url(#${id})`} />
    </Svg>
  </Animated.View>;
}
const BEAM_W = 200;

/**
 * The cheer squad in a champion's Trophy Cabinet. Two cheerleaders carry the Congratulations banner over their heads
 * and run the routine (stand, knee, kick, lunge) while the lead dances in front of them (star jumps, kicks, hip sways,
 * full turns). Fireworks and stage lights grow with the squad level. Scrolls on short phones so the buttons stay reachable.
 */
export function CheerSquad({ visible, name, avatar, frame, crown, level: lv = 1, title, onClose }: {
  visible: boolean; name: string; avatar?: string | null; frame?: string | null; crown: { won: number; real: number }; level?: number; title?: string; onClose: () => void;
}) {
  const { width: W, height: H } = useWindowDimensions();
  const reduced = !!useReducedMotion();
  const level = (LOOK[lv as Level] ? lv : 1) as Level, look = LOOK[level], geo = SQUAD_GEO[level];
  const clock = useSharedValue(0), glitter = useSharedValue(0), wave = useSharedValue(0), sweep = useSharedValue(0), lights = useSharedValue(0);
  const [round, setRound] = useState(0);
  useEffect(() => {
    if (!visible || reduced) return;
    const loop = (v: SharedValue<number>, ms: number, back = false) => { v.value = 0; v.value = withRepeat(withTiming(1, { duration: ms, easing: Easing.linear }), -1, back); };
    loop(clock, COUNT * BEAT); loop(glitter, 1900); loop(wave, 1600); loop(sweep, 2300); loop(lights, 6000);
    return () => { [clock, glitter, wave, sweep, lights].forEach((v) => cancelAnimation(v)); };
  }, [visible, reduced, round]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!visible) return;
    playSfx(round ? "combo" : level >= 3 ? "levelup" : "win");
    if (Platform.OS !== "web") Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
  }, [visible, round, level]);

  // The stage: the banner hangs between the holders' raised fists (their grip points), the lead dances in front.
  const SW = Math.min(W - 12, 620), bw = Math.min(SW * 0.6, 520), gl = (SW - bw) / 2, gr = gl + bw;
  const Hh = Math.max(150, Math.min(H * 0.32, 250, SW * 0.62, (H - 470) / 1.1)), Hl = Hh * 0.95;
  const bh = Math.max(86, Math.min(124, bw * 0.42)), medal = Math.min(58, bh * 0.62);
  const ga = geo.a.grip, gb = geo.b.grip, wa = Hh * geo.a.aspect, wb = Hh * geo.b.aspect;
  const top = bh + medal / 2 + Hh * 0.08 + 6 - Math.min(ga[0][1], gb[0][1]) * Hh; // room above the holders for the banner
  const SH = top + Hh * 1.1;
  const leftA = gl - ga[0][0] * wa, leftB = gr - (1 - gb[0][0]) * wb;
  // Where the holders' hands are in each pose. Kept as plain numbers: on a phone this animation runs on the UI thread,
  // which cannot call an ordinary app function (doing so closes the installed app; the browser preview never shows it).
  const hands = ga.map((g, p) => ((g[1] + gb[p][1]) / 2) * Hh);
  const carry = useAnimatedStyle(() => {
    const x = clock.value * COUNT, n = Math.floor(x) % COUNT, k = x - Math.floor(x), p = HOLD_SEQ[n];
    const tilt = Math.atan2((gb[p][1] - ga[p][1]) * Hh, bw) * (180 / Math.PI);
    return { transform: [{ translateY: hands[p] - hands[0] - Math.sin(k * Math.PI) * HOLD_HOP[n] * Hh }, { rotate: `${tilt + Math.sin(wave.value * Math.PI * 2) * 0.8}deg` }] };
  });
  const bursts = Array.from({ length: look.bursts }, (_, i) => ({ x: SW * (0.12 + ((i * 0.37) % 0.78)), y: 18 + ((i * 53) % Math.max(40, top - bh)), size: 70 + ((i * 29) % 50), color: GEMS[i % GEMS.length], delay: i * 330 }));
  return <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose} statusBarTranslucent>
    <View testID="cheer-squad" style={styles.flex}>
      <Image source={ARENA} style={StyleSheet.absoluteFill} contentFit="cover" />
      <LinearGradient pointerEvents="none" colors={[arena.scrim, arena.shade, arena.scrim]} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFill} />
      {look.tint ? <View pointerEvents="none" style={[StyleSheet.absoluteFill, { backgroundColor: look.tint }]} /> : null}
      {look.beams.map((c, i) => <Beam key={i} x={W * ((i + 0.5) / look.beams.length)} color={c} clock={lights} height={H * 0.95} phase={i / look.beams.length} />)}
      <ScrollView style={styles.flex} contentContainerStyle={styles.root} showsVerticalScrollIndicator={false} bounces={false}>
        <Pop><View testID="cheer-level" style={styles.pill}><T w="heavy" size={11} color={arena.badgeInk} style={styles.spaced}>LEVEL {level} · {(title || "Rookie Squad").toUpperCase()}</T></View></Pop>
        <View testID="cheer-stage" style={{ width: SW, height: SH, alignSelf: "center" }}>
          {bursts.map((b, i) => <Burst key={i} {...b} testID={i ? undefined : "cheer-burst"} />)}
          {/* The lead dances under the banner so her pom-poms never hide the champion's name. */}
          <Dancer testID="cheer-lead" frames={squadFrames(level, "c")} height={Hl} aspect={geo.c.aspect} clock={clock} seq={LEAD_SEQ} hops={LEAD_HOP} spins={LEAD_SPIN}
            style={{ left: SW / 2 - (Hl * geo.c.aspect) / 2, top: SH - Hl }} />
          <Animated.View style={[styles.carry, { left: gl - 4, top: top + hands[0] - bh, width: bw + 8 }, carry]}>
            <Pole side="left" level={level} height={bh + 30} />
            <Pole side="right" level={level} height={bh + 30} />
            <View style={styles.bannerAt}><CheerBanner w={bw} h={bh} top={medal / 2} level={level} name={name} crown={crown} clock={clock} count={COUNT} glitter={glitter} wave={wave} sweep={sweep} /></View>
            <View style={[styles.medal, { top: -medal / 2, left: bw / 2 + 4 - medal / 2 }]}>
              <Avatar icon={avatar} frame={frame} size={medal} />
              <View style={[styles.medalCrown, { top: -medal * 0.5 }]}><CrownArt size={medal * 0.7} gold={crown.real > 0} /></View>
            </View>
          </Animated.View>
          <Dancer testID="cheer-holder-1" frames={squadFrames(level, "a")} height={Hh} aspect={geo.a.aspect} clock={clock} seq={HOLD_SEQ} hops={HOLD_HOP} style={{ left: leftA, top }} />
          <Dancer testID="cheer-holder-2" frames={squadFrames(level, "b")} height={Hh} aspect={geo.b.aspect} clock={clock} seq={HOLD_SEQ} hops={HOLD_HOP} flip style={{ left: leftB, top }} />
          <Twinkles spots={[[6, 30, 16], [94, 26, 14], [50, 2, 12], [14, 70, 10], [86, 66, 12], [30, 12, 10], [70, 14, 10]]} color={level === 4 ? gemColors.kohinoor : arena.gold} />
        </View>
        <Pop delay={400}><T testID="cheer-line" w="bold" size={14} color={arena.text} style={styles.centerText}>The {title || "Rookie Squad"} is dancing for {name}! {crown.won > 1 ? `${crown.won} cups won and counting.` : "A Knockout Cup champion."}</T></Pop>
        <View style={styles.buttons}>
          <RaisedButton testID="cheer-again" glyph="party-popper" height={60} streak label="CHEER AGAIN" sub="Louder this time!" onPress={() => setRound((n) => n + 1)} />
          <RaisedButton testID="cheer-close" tone="wine" label="Continue" onPress={onClose} />
        </View>
      </ScrollView>
      <Confetti key={round} count={level >= 3 ? 72 : 56} />
    </View>
  </Modal>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, centerText: { textAlign: "center" }, spaced: { letterSpacing: 1.6 },
  root: { flexGrow: 1, justifyContent: "center", paddingHorizontal: 6, paddingTop: 40, paddingBottom: 28, gap: 10 },
  pill: { alignSelf: "center", paddingHorizontal: 14, height: 28, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: arena.gold, borderWidth: 1.5, borderColor: arena.goldDeep },
  beam: { position: "absolute", top: -10, width: BEAM_W },
  carry: { position: "absolute" },
  bannerAt: { marginHorizontal: 4 },
  medal: { position: "absolute", alignItems: "center" },
  medalCrown: { position: "absolute", left: 0, right: 0, alignItems: "center" },
  shadow: { position: "absolute", bottom: 0, backgroundColor: arena.black },
  buttons: { alignSelf: "center", gap: 10, maxWidth: 460, width: "100%", paddingHorizontal: 10 },
});
