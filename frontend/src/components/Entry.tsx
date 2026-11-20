import React, { useEffect, useId, useState } from "react";
import { Platform, StyleSheet, View, useWindowDimensions } from "react-native";
import { Image } from "expo-image";
import * as Haptics from "expo-haptics";
import Animated, { Easing, Extrapolation, SharedValue, cancelAnimation, interpolate, runOnJS, useAnimatedStyle, useReducedMotion, useSharedValue, withRepeat, withTiming } from "react-native-reanimated";
import { LinearGradient } from "expo-linear-gradient";
import Svg, { Circle, Defs, Path, RadialGradient, Stop } from "react-native-svg";
import { Icon, T } from "@/src/components/ui";
import { AVATAR_IMAGES } from "@/src/avatars";
import { Emblem, PhoenixDiamond } from "@/src/rapid/Art";
import { rnd } from "@/src/rapid/juice";
import { playSfx } from "@/src/sfx";
import { arena, fx, gemColors } from "@/src/theme";

/** The original Colosseum of Rome, packed and roaring: every entry show happens on its sand. */
const COLOSSEUM = require("../../assets/arena/bg_colosseum.webp");

export const FRAME_COLORS: Record<string, [string, string]> = {
  frame_gold: [arena.gold, arena.goldDeep], frame_neon: [fx.bolt, arena.teal], frame_fire: [fx.ember, fx.fire], frame_diamond: [fx.white, fx.ice],
  // Diamond specials, paid with streak diamonds.
  frame_ruby: [gemColors.red, fx.fire], frame_sapphire: [fx.bolt, gemColors.blue], frame_emerald: [gemColors.emerald, arena.teal], frame_kohinoor: [gemColors.kohinoor, gemColors.gold],
};
const STILL_FRAMES = ["frame_gold"];
const CROWNED = ["frame_diamond", "frame_kohinoor"];

// Avatar: 3D hero portrait with an optional purchased frame (animated pulse for neon/fire/diamond frames).
export function Avatar({ icon, frame, size = 56, testID }: { icon?: string | null; frame?: string | null; size?: number; testID?: string }) {
  const reduced = useStill();
  const pulse = useSharedValue(1);
  useEffect(() => {
    cancelAnimation(pulse);
    pulse.value = 1;
    if (!reduced && frame && FRAME_COLORS[frame] && !STILL_FRAMES.includes(frame)) pulse.value = withRepeat(withTiming(1.08, { duration: 900 }), -1, true);
  }, [frame, reduced, pulse]);
  const a = useAnimatedStyle(() => ({ transform: [{ scale: pulse.value }] }));
  const ring = (frame && FRAME_COLORS[frame]) || [arena.rimHi, arena.rim];
  return (
    <Animated.View testID={testID} style={[{ width: size, height: size }, a]}>
      <LinearGradient colors={ring as [string, string]} style={{ flex: 1, borderRadius: size / 2, padding: frame ? Math.max(3, size / 22) : 2 }}>
        <View style={{ flex: 1, borderRadius: size / 2, backgroundColor: arena.panelHi, overflow: "hidden" }}>
          <Image source={AVATAR_IMAGES[icon || ""] || AVATAR_IMAGES.av_robo} style={styles.fill} contentFit="cover" transition={120} />
        </View>
      </LinearGradient>
      {frame && CROWNED.includes(frame) ? <View style={styles.crown}><Icon name="crown" size={size * 0.34} color={arena.gold} /></View> : null}
    </Animated.View>
  );
}

type Motion = "radial" | "rise" | "fall" | "swirlIn" | "swirlOut" | "streak" | "spiral";
type Effect = { label: string; icon: string; c1: string; c2: string; motion: Motion; from: "left" | "right" | "top" | "bottom"; sfx: string };
// Players who never picked an entry effect arrive with this one.
export const ROYAL: Effect = { label: "Royal", icon: "crown", c1: fx.gold, c2: fx.white, motion: "fall", from: "top", sfx: "entry_crown" };
export const EFFECTS: Record<string, Effect> = {
  entry_spark: { label: "Neon Spark", icon: "star-four-points", c1: fx.ice, c2: fx.white, motion: "radial", from: "bottom", sfx: "entry_spark" },
  entry_rocket: { label: "Rocket Launch", icon: "rocket-launch", c1: fx.fire, c2: fx.ember, motion: "rise", from: "bottom", sfx: "entry_rocket" },
  entry_lightning: { label: "Thunder Strike", icon: "lightning-bolt", c1: fx.bolt, c2: fx.white, motion: "radial", from: "top", sfx: "entry_lightning" },
  entry_supercar: { label: "Supercar Drift", icon: "car-sports", c1: fx.fire, c2: fx.smoke, motion: "streak", from: "right", sfx: "entry_supercar" },
  entry_crown: { label: "Royal Parade", icon: "crown", c1: fx.gold, c2: fx.ember, motion: "fall", from: "top", sfx: "entry_crown" },
  entry_tornado: { label: "Cyclone Spin", icon: "weather-tornado", c1: fx.ice, c2: fx.smoke, motion: "spiral", from: "bottom", sfx: "entry_tornado" },
  entry_meteor: { label: "Meteor Crash", icon: "meteor", c1: fx.fire, c2: fx.crimson, motion: "radial", from: "top", sfx: "entry_meteor" },
  entry_dragon: { label: "Dragon Inferno", icon: "fire", c1: fx.crimson, c2: fx.fire, motion: "rise", from: "left", sfx: "entry_dragon" },
  entry_phoenix: { label: "Phoenix Rise", icon: "bird", c1: fx.ember, c2: fx.fire, motion: "rise", from: "bottom", sfx: "entry_phoenix" },
  entry_galaxy: { label: "Galaxy Warp", icon: "orbit", c1: fx.sky, c2: fx.ice, motion: "swirlOut", from: "right", sfx: "entry_galaxy" },
  entry_blackhole: { label: "Black Hole", icon: "atom-variant", c1: fx.white, c2: fx.sky, motion: "swirlIn", from: "top", sfx: "entry_blackhole" },
  // Diamond specials, paid with streak diamonds.
  entry_ruby: { label: "Ruby Storm", icon: "diamond-stone", c1: gemColors.red, c2: fx.white, motion: "fall", from: "top", sfx: "entry_meteor" },
  entry_sapphire: { label: "Sapphire Comet", icon: "diamond-stone", c1: gemColors.blue, c2: fx.bolt, motion: "streak", from: "right", sfx: "entry_galaxy" },
  entry_emerald: { label: "Emerald Surge", icon: "diamond-stone", c1: gemColors.emerald, c2: fx.ice, motion: "rise", from: "bottom", sfx: "entry_phoenix" },
  entry_kohinoor: { label: "Kohinoor Nova", icon: "diamond-stone", c1: gemColors.kohinoor, c2: gemColors.gold, motion: "swirlOut", from: "top", sfx: "entry_blackhole" },
};
export const effectOf = (id?: string | null) => (id && EFFECTS[id]) || ROYAL;

export const BUILD = 0.5, EACH = 3.5, VS = 1.3, FIGHT = 0.7;
/** Length of the show in seconds: 2 players = 9.5, 5 players = 20. */

const N = 30;
const heavy = () => { if (Platform.OS !== "web") Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy).catch(() => {}); };

function Particle({ i, clock, start, motion, color, w, h }: { i: number; clock: SharedValue<number>; start: number; motion: Motion; color: string; w: number; h: number }) {
  const r1 = rnd(i, 1), r2 = rnd(i, 2), size = 6 + r1 * 14;
  const st = useAnimatedStyle(() => {
    const t = Math.min(1, Math.max(0, (clock.value - start - 0.5 - r2 * 0.5) / 2.2));
    const ang = (i / N) * Math.PI * 2 + r2;
    let x = 0, y = 0;
    if (motion === "radial") { x = Math.cos(ang) * t * w * (0.4 + r1 * 0.4); y = Math.sin(ang) * t * h * (0.3 + r1 * 0.3); }
    else if (motion === "rise") { x = (r1 - 0.5) * w + Math.sin(t * 6 + i) * 18; y = h * 0.5 - t * h * (0.7 + r2 * 0.5); }
    else if (motion === "fall") { x = (r1 - 0.5) * w; y = -h * 0.55 + t * h * (0.8 + r2 * 0.4); }
    else if (motion === "streak") { x = w * 0.7 - t * w * (1.3 + r2); y = (r1 - 0.5) * h * 0.7; }
    else if (motion === "spiral") { const a = ang + t * 10; const rr = 40 + t * w * 0.5; x = Math.cos(a) * rr; y = h * 0.35 - t * h * 0.7 + Math.sin(a) * 30; }
    else { const a = ang + t * (motion === "swirlIn" ? -9 : 7); const rr = motion === "swirlIn" ? (1 - t) * w * 0.7 : t * w * 0.65; x = Math.cos(a) * rr; y = Math.sin(a) * rr * 0.8; }
    return { opacity: t <= 0 ? 0 : interpolate(t, [0, 0.12, 0.75, 1], [0, 1, 0.9, 0]), transform: [{ translateX: x }, { translateY: y }, { scale: motion === "streak" ? 1 : 1 - t * 0.4 }] };
  });
  const streak = motion === "streak";
  return <Animated.View pointerEvents="none" style={[{ position: "absolute", width: streak ? 60 + r1 * 110 : size, height: streak ? 4 : size, borderRadius: size, backgroundColor: color, shadowColor: color, shadowOpacity: 1, shadowRadius: 10 }, st]} />;
}

const RAYS = Array.from({ length: 12 }, (_, i) => i * 30);
/** Twelve beams of light fanning out from the player, with a soft glow in the middle. Drawn once; the wrapper turns it. */
const Beams = React.memo(function Beams({ size, color }: { size: number; color: string }) {
  const r = size / 2, id = "entryGlow" + useId().replace(/[^a-zA-Z0-9]/g, "");
  return <Svg width={size} height={size} viewBox={`${-r} ${-r} ${size} ${size}`}>
    {/* Explicit stopOpacity: native SVG ignores alpha inside stopColor. */}
    <Defs><RadialGradient id={id} cx="0" cy="0" r={r * 0.42} gradientUnits="userSpaceOnUse"><Stop offset="0" stopColor={color} stopOpacity={0.75} /><Stop offset="1" stopColor={color} stopOpacity={0} /></RadialGradient></Defs>
    {RAYS.map((deg) => <Path key={deg} d={`M0 0 L${-r * 0.12} ${-r} L${r * 0.12} ${-r} Z`} fill={color} opacity={deg % 60 ? 0.13 : 0.26} transform={`rotate(${deg})`} />)}
    <Circle r={r * 0.42} fill={`url(#${id})`} />
  </Svg>;
});

// `emblem` makes this a gang's entry in a Gang Battle: the whole team arrives as one, under its emblem, with `sub` as its second line.
export type EntryPlayer = { name?: string; avatar?: string | null; frame?: string | null; entry?: string | null; level?: number; wins?: number; you?: boolean; bot?: boolean; emblem?: string | null; sub?: string };
const who = (p: EntryPlayer) => (p.emblem ? p.name : p.you ? "You" : p.name) || "Rival";
const face = (p: EntryPlayer, size: number) => (p.emblem ? <Emblem id={p.emblem} size={size} /> : <Avatar icon={p.avatar} frame={p.frame} size={size} />);

// One player's full-screen 3.5 seconds: the effect fills the screen, the avatar slams down, the nameplate rises.
function PlayerEntry({ p, start, clock, W, H, reduced }: { p: EntryPlayer; start: number; clock: SharedValue<number>; W: number; H: number; reduced: boolean }) {
  const e = effectOf(p.entry);
  const size = Math.min(W * 0.52, 230);
  const far = e.from === "left" ? -W : e.from === "right" ? W : e.from === "top" ? -H * 0.7 : H * 0.7;
  const side = e.from === "left" || e.from === "right";
  const tint = useAnimatedStyle(() => ({ opacity: interpolate(clock.value - start, [0, 0.2, 3.1, 3.5], [0, 1, 1, 0], Extrapolation.CLAMP) }));
  const glyph = useAnimatedStyle(() => {
    const u = clock.value - start;
    const spin = e.motion === "swirlIn" || e.motion === "swirlOut" || e.motion === "spiral" ? u * 90 : 0;
    return { opacity: interpolate(u, [0, 0.3, 2.8, 3.4], [0, 0.42, 0.3, 0], Extrapolation.CLAMP), transform: [{ scale: reduced ? 1.6 : interpolate(u, [0, 0.6, 3.5], [0.4, 1.6, 2.3], Extrapolation.CLAMP) }, { rotate: `${reduced ? 0 : spin}deg` }] };
  });
  const body = useAnimatedStyle(() => {
    const u = clock.value - start;
    const o = interpolate(u, [0.1, 0.3, 3.1, 3.45], [0, 1, 1, 0], Extrapolation.CLAMP);
    if (reduced) return { opacity: o };
    const t = Math.min(1, Math.max(0, (u - 0.15) / 0.55)), pos = far * Math.pow(1 - t, 3);
    return { opacity: o, transform: [side ? { translateX: pos } : { translateY: pos }, { scale: interpolate(u, [0.15, 0.7, 0.82, 1, 3.1, 3.5], [0.5, 1.28, 0.94, 1, 1, 1.4], Extrapolation.CLAMP) }] };
  });
  const plate = useAnimatedStyle(() => {
    const u = clock.value - start;
    return { opacity: interpolate(u, [1, 1.3, 3.1, 3.4], [0, 1, 1, 0], Extrapolation.CLAMP), transform: [{ translateY: reduced ? 0 : interpolate(u, [1, 1.3], [30, 0], Extrapolation.CLAMP) }] };
  });
  const flash = useAnimatedStyle(() => ({ opacity: reduced ? 0 : interpolate(clock.value - start, [0.66, 0.72, 0.95], [0, 0.28, 0], Extrapolation.CLAMP) })); // a quick spark, never a white-out over the Colosseum
  // The landing: beams of light burst out behind the avatar and keep turning, and a shockwave ring races outwards.
  const beamSize = Math.max(W, H) * 1.5;
  const beams = useAnimatedStyle(() => {
    const u = clock.value - start;
    // Lighter over the Colosseum, so the arena stays visible behind the burst.
    return { opacity: interpolate(u, [0.6, 0.85, 3.05, 3.4], [0, 0.6, 0.6, 0], Extrapolation.CLAMP), transform: [{ rotate: `${reduced ? 0 : u * 20}deg` }, { scale: reduced ? 1 : interpolate(u, [0.6, 0.95], [0.25, 1], Extrapolation.CLAMP) }] };
  });
  const wave = useAnimatedStyle(() => {
    const u = clock.value - start;
    return { opacity: reduced ? 0 : interpolate(u, [0.68, 0.74, 1.55], [0, 0.95, 0], Extrapolation.CLAMP), transform: [{ scale: interpolate(u, [0.68, 1.55], [0.7, 3.4], Extrapolation.CLAMP) }] };
  });
  return <View pointerEvents="none" style={[StyleSheet.absoluteFill, styles.centered]}>
    <Animated.View style={[StyleSheet.absoluteFill, tint]}><LinearGradient colors={[e.c1, arena.clear, arena.clear, e.c1]} locations={[0, 0.38, 0.66, 1]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[StyleSheet.absoluteFill, styles.tint]} /></Animated.View>
    <Animated.View style={[styles.glyph, glyph]}><Icon name={e.icon as any} size={W * 0.8} color={e.c1} /></Animated.View>
    <Animated.View style={[styles.glyph, beams]}><Beams size={beamSize} color={e.c1} /></Animated.View>
    {reduced ? null : Array.from({ length: N }, (_, i) => <Particle key={i} i={i} clock={clock} start={start} motion={e.motion} color={i % 3 ? e.c1 : e.c2} w={W} h={H} />)}
    <Animated.View style={[styles.glyph, { width: size, height: size, borderRadius: size / 2, borderWidth: 5, borderColor: e.c2 }, wave]} />
    <Animated.View style={[styles.centered, body]}>{face(p, size)}</Animated.View>
    <Animated.View style={[styles.plate, { borderColor: e.c1 }, plate]}>
      <T w="heavy" size={26} color={arena.text} numberOfLines={1} style={styles.center}>{who(p)}</T>
      <T w="bold" size={14} color={arena.gold} style={styles.center}>{p.sub || `Level ${p.level ?? 1} · ${p.wins ?? 0} win${p.wins === 1 ? "" : "s"}${p.bot ? " · Practice rival" : ""}`}</T>
      <T w="heavy" size={11} color={e.c1} style={[styles.center, styles.spaced]}>{e.label.toUpperCase()} ENTRY</T>
    </Animated.View>
    <Animated.View style={[StyleSheet.absoluteFill, { backgroundColor: e.c2 }, flash]} />
  </View>;
}

/**
 * Entry show before every match: dark build-up, 3.5 seconds for each player (you first), VS slam in front of the
 * Phoenix Diamond, FIGHT. `elapsed` is how far into the show the server clock already is, so every phone stays in step.
 * `solo` plays just one entry (profile "Watch entry", store preview).
 */
export function EntryShow({ players, elapsed = 0, solo, onDone, testID = "entry-show" }: { players: EntryPlayer[]; elapsed?: number; solo?: boolean; onDone?: () => void; testID?: string }) {
  const { width: W, height: H } = useWindowDimensions();
  const reduced = !!useReducedMotion();
  const n = players.length;
  const vsAt = BUILD + EACH * n, fightAt = vsAt + VS, end = solo ? vsAt : fightAt + FIGHT;
  const clock = useSharedValue(elapsed);
  const [phase, setPhase] = useState(-1);
  useEffect(() => {
    const cues: [number, () => void][] = [];
    players.forEach((p, i) => {
      const at = BUILD + EACH * i;
      cues.push([at, () => { setPhase(i); playSfx(effectOf(p.entry).sfx, i ? 0.85 : 1); }], [at + 0.72, heavy]);
    });
    if (!solo) cues.push([vsAt, () => setPhase(n)], [vsAt + 0.5, () => { playSfx("vs"); heavy(); }], [fightAt, () => playSfx("go", 0.8)]);
    const late = cues.filter(([at]) => at <= elapsed).map(([, run]) => run);
    if (late.length) setPhase(Math.min(n, Math.max(0, Math.floor((elapsed - BUILD) / EACH))));
    const timers = cues.filter(([at]) => at > elapsed).map(([at, run]) => setTimeout(run, (at - elapsed) * 1000));
    clock.value = withTiming(end, { duration: Math.max(0, end - elapsed) * 1000, easing: Easing.linear }, (f) => { if (f && onDone) runOnJS(onDone)(); });
    return () => { timers.forEach(clearTimeout); cancelAnimation(clock); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const root = useAnimatedStyle(() => {
    let shake = 0;
    if (!reduced) {
      for (let i = 0; i <= n; i++) {
        const dt = clock.value - (i < n ? BUILD + EACH * i + 0.72 : vsAt + 0.55);
        if (dt > 0 && dt < 0.35 && (i < n || !solo)) shake += Math.sin(dt * 70) * 11 * (1 - dt / 0.35);
      }
    }
    return { opacity: interpolate(clock.value, [end - 0.18, end], [1, 0], Extrapolation.CLAMP), transform: [{ translateX: shake }] };
  });
  const ring = useAnimatedStyle(() => ({ opacity: interpolate(clock.value, [0, 0.4, 0.7], [0, 0.9, 0], Extrapolation.CLAMP), transform: [{ scale: interpolate(clock.value, [0, 0.7], [0.2, 2.4], Extrapolation.CLAMP) }] }));
  const lineup = useAnimatedStyle(() => ({ opacity: interpolate(clock.value - vsAt, [0, 0.25], [0, 1], Extrapolation.CLAMP) }));
  const gem = useAnimatedStyle(() => ({ transform: [{ scale: reduced ? 1 : interpolate(clock.value - vsAt, [0, 0.4], [0.3, 1], Extrapolation.CLAMP) }] }));
  const vs = useAnimatedStyle(() => {
    const v = clock.value - vsAt;
    return { opacity: v > 0.3 ? 1 : 0, transform: [{ scale: reduced ? 1 : interpolate(v, [0.3, 0.55, 0.7], [3.4, 0.9, 1], Extrapolation.CLAMP) }, { rotate: `${reduced ? 0 : interpolate(v, [0.3, 0.55], [-22, 0], Extrapolation.CLAMP)}deg` }] };
  });
  const slam = useAnimatedStyle(() => ({ opacity: reduced ? 0 : interpolate(clock.value - vsAt, [0.5, 0.56, 0.95], [0, 0.85, 0], Extrapolation.CLAMP) }));
  const fight = useAnimatedStyle(() => {
    const f = clock.value - fightAt;
    return { opacity: f > 0 ? 1 : 0, transform: [{ scale: reduced ? 1 : interpolate(f, [0, 0.2, 0.32], [0.3, 1.15, 1], Extrapolation.CLAMP) }] };
  });
  const seat = Math.min(96, (W - 32) / n - 10);
  // The camera pushes slowly into the arena for the whole show.
  const push = useAnimatedStyle(() => ({ transform: [{ scale: reduced ? 1.04 : interpolate(clock.value, [0, end], [1.04, 1.18], Extrapolation.CLAMP) }] }));

  return (
    <Animated.View testID={testID} accessibilityLabel="Entry show" style={[StyleSheet.absoluteFill, styles.root, root]}>
      <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFill, push]}><Image testID={`${testID}-colosseum`} source={COLOSSEUM} style={styles.fill} contentFit="cover" contentPosition="center" /></Animated.View>
      <LinearGradient pointerEvents="none" colors={[arena.shade, arena.clear, arena.clear, arena.scrim]} locations={[0, 0.3, 0.6, 1]} style={StyleSheet.absoluteFill} />
      <Animated.View pointerEvents="none" style={[styles.ring, ring]} />
      {phase >= 0 && phase < n ? <PlayerEntry key={phase} p={players[phase]} start={BUILD + EACH * phase} clock={clock} W={W} H={H} reduced={reduced} /> : null}
      {phase >= n && !solo ? <Animated.View testID="entry-versus" style={[StyleSheet.absoluteFill, styles.centered, lineup]}>
        <LinearGradient pointerEvents="none" colors={[arena.scrim, arena.shade, arena.scrim]} locations={[0.12, 0.52, 0.92]} style={StyleSheet.absoluteFill} />
        <Animated.View style={[styles.gem, gem]}><PhoenixDiamond width={Math.min(W * 0.82, 340)} /></Animated.View>
        <View style={styles.seats}>
          {players.map((p, i) => <View key={i} style={[styles.seat, { width: seat + 8 }]}>
            {face(p, seat)}
            <T w="heavy" size={n > 3 ? 11 : 13} color={p.you ? arena.gold : arena.text} numberOfLines={1}>{who(p)}</T>
          </View>)}
        </View>
        <Animated.View style={vs}><T w="heavy" size={84} color={arena.gold} style={styles.vs}>VS</T></Animated.View>
        <Animated.View style={[styles.fight, fight]}><T w="heavy" size={50} color={arena.text} style={styles.fightText} testID="entry-fight">FIGHT!</T></Animated.View>
        <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFill, { backgroundColor: arena.gold }, slam]} />
      </Animated.View> : null}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  fill: { width: "100%", height: "100%" }, crown: { position: "absolute", top: -8, alignSelf: "center" },
  root: { zIndex: 50, backgroundColor: arena.black }, centered: { alignItems: "center", justifyContent: "center" }, center: { textAlign: "center" },
  tint: { opacity: 0.4 }, glyph: { position: "absolute" }, spaced: { letterSpacing: 2.5 },
  ring: { position: "absolute", alignSelf: "center", top: "42%", width: 180, height: 180, borderRadius: 90, borderWidth: 6, borderColor: arena.gold },
  plate: { position: "absolute", bottom: "13%", left: 24, right: 24, paddingVertical: 14, paddingHorizontal: 16, borderRadius: 20, borderWidth: 2, backgroundColor: arena.scrim, gap: 4 },
  gem: { position: "absolute" }, seats: { position: "absolute", top: "17%", left: 16, right: 16, flexDirection: "row", justifyContent: "space-around" }, seat: { alignItems: "center", gap: 6 },
  vs: { letterSpacing: 4, textShadowColor: arena.bgDeep, textShadowOffset: { width: 0, height: 5 }, textShadowRadius: 2 },
  fight: { position: "absolute", bottom: "16%" }, fightText: { letterSpacing: 5, textShadowColor: fx.fire, textShadowRadius: 18 },
});
