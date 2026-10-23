import React, { useEffect } from "react";
import { StyleSheet, View, useWindowDimensions } from "react-native";
import { Image } from "expo-image";
import Animated, {
  Easing, SharedValue, cancelAnimation, interpolate, runOnJS, useAnimatedStyle, useReducedMotion, useSharedValue,
  withDelay, withRepeat, withSequence, withSpring, withTiming,
} from "react-native-reanimated";
import { LinearGradient } from "expo-linear-gradient";
import { Icon, T } from "@/src/components/ui";
import { AVATAR_IMAGES } from "@/src/avatars";
import { playSfx } from "@/src/sfx";
import { colors } from "@/src/theme";

export const FRAME_COLORS: Record<string, [string, string]> = {
  frame_gold: [colors.custom_neonAmber, colors.custom_amber],
  frame_neon: [colors.custom_neonCyan, colors.brandPrimary],
  frame_fire: [colors.custom_examBitsat, colors.custom_examJee],
  frame_diamond: [colors.custom_neonCyan, colors.custom_neonAmber],
};

// Avatar: 3D hero portrait with an optional purchased frame (animated pulse for neon/fire/diamond frames).
export function Avatar({ icon, frame, size = 56, testID }: { icon?: string | null; frame?: string | null; size?: number; testID?: string }) {
  const reduced = useReducedMotion();
  const pulse = useSharedValue(1);
  useEffect(() => {
    cancelAnimation(pulse);
    pulse.value = 1;
    if (!reduced && (frame === "frame_neon" || frame === "frame_diamond" || frame === "frame_fire")) pulse.value = withRepeat(withTiming(1.08, { duration: 900 }), -1, true);
  }, [frame, reduced, pulse]);
  const a = useAnimatedStyle(() => ({ transform: [{ scale: pulse.value }] }));
  const ring = frame ? FRAME_COLORS[frame] : [colors.custom_gameLine, colors.custom_gameLine];
  const img = icon ? AVATAR_IMAGES[icon] : AVATAR_IMAGES.av_robo;
  return (
    <Animated.View testID={testID} style={[{ width: size, height: size }, a]}>
      <LinearGradient colors={ring as [string, string]} style={{ flex: 1, borderRadius: size / 2, padding: frame ? 3 : 2 }}>
        <View style={{ flex: 1, borderRadius: size / 2, backgroundColor: colors.custom_gameCardHi, alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
          {img ? <Image source={img} style={{ width: "100%", height: "100%" }} contentFit="cover" transition={120} /> : <Icon name={icon as any} size={size * 0.55} color={colors.onSurfaceInverse} />}
        </View>
      </LinearGradient>
      {frame === "frame_diamond" ? <View style={{ position: "absolute", top: -8, alignSelf: "center" }}><Icon name="crown" size={size * 0.34} color={colors.custom_neonAmber} /></View> : null}
    </Animated.View>
  );
}

type Motion = "radial" | "rise" | "fall" | "swirlIn" | "swirlOut" | "streak" | "spiral";
export const EFFECTS: Record<string, { icon: string; c1: string; c2: string; motion: Motion }> = {
  entry_rocket: { icon: "rocket-launch", c1: colors.custom_examBitsat, c2: colors.custom_neonAmber, motion: "rise" },
  entry_lightning: { icon: "lightning-bolt", c1: colors.custom_neonCyan, c2: colors.onSurfaceInverse, motion: "radial" },
  entry_supercar: { icon: "car-sports", c1: colors.custom_examBitsat, c2: colors.custom_neonRed, motion: "streak" },
  entry_crown: { icon: "crown", c1: colors.custom_neonAmber, c2: colors.custom_examComedkGold, motion: "fall" },
  entry_tornado: { icon: "weather-tornado", c1: colors.custom_neonCyan, c2: colors.custom_gameMuted, motion: "spiral" },
  entry_meteor: { icon: "meteor", c1: colors.custom_examBitsat, c2: colors.custom_examJee, motion: "radial" },
  entry_dragon: { icon: "fire", c1: colors.custom_examJee, c2: colors.custom_examBitsat, motion: "rise" },
  entry_phoenix: { icon: "bird", c1: colors.custom_neonAmber, c2: colors.custom_examBitsat, motion: "rise" },
  entry_galaxy: { icon: "orbit", c1: colors.custom_neonViolet, c2: colors.custom_neonMagenta, motion: "swirlOut" },
  entry_blackhole: { icon: "atom-variant", c1: colors.custom_neonViolet, c2: colors.custom_gameBg, motion: "swirlIn" },
};

const N = 22;
const rnd = (i: number, k: number) => { const x = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x); };

function Particle({ i, p, motion, color, w, h }: { i: number; p: SharedValue<number>; motion: Motion; color: string; w: number; h: number }) {
  const r1 = rnd(i, 1), r2 = rnd(i, 2), size = 4 + r1 * 9;
  const st = useAnimatedStyle(() => {
    const t = p.value;
    let x = 0, y = 0, o = interpolate(t, [0, 0.15, 0.75, 1], [0, 1, 0.9, 0]);
    const ang = (i / N) * Math.PI * 2 + r2;
    if (motion === "radial") { x = Math.cos(ang) * t * w * (0.35 + r1 * 0.3); y = Math.sin(ang) * t * h * (0.25 + r1 * 0.2); }
    else if (motion === "rise") { x = (r1 - 0.5) * w * 0.8 + Math.sin(t * 6 + i) * 14; y = h * 0.3 - t * h * (0.5 + r2 * 0.4); }
    else if (motion === "fall") { x = (r1 - 0.5) * w * 0.9; y = -h * 0.4 + t * h * (0.5 + r2 * 0.3); }
    else if (motion === "streak") { x = w * 0.6 - t * w * (1.2 + r2); y = (r1 - 0.5) * h * 0.4; }
    else if (motion === "spiral") { const a = ang + t * 10; const rr = 30 + t * w * 0.35; x = Math.cos(a) * rr * 0.6; y = h * 0.2 - t * h * 0.45 + Math.sin(a) * 18; }
    else { const a = ang + t * (motion === "swirlIn" ? -9 : 7); const rr = motion === "swirlIn" ? (1 - t) * w * 0.55 : t * w * 0.5; x = Math.cos(a) * rr; y = Math.sin(a) * rr * 0.6; }
    return { opacity: o, transform: [{ translateX: x }, { translateY: y }, { scale: motion === "streak" ? 1 : 1 - t * 0.4 }] };
  });
  const streak = motion === "streak";
  return <Animated.View pointerEvents="none" style={[{ position: "absolute", width: streak ? 30 + r1 * 50 : size, height: streak ? 3 : size, borderRadius: size, backgroundColor: color, shadowColor: color, shadowOpacity: 1, shadowRadius: 8 }, st]} />;
}

// One effect "burst": particles + a giant glowing effect icon behind the player.
function Burst({ effect, p, w, h }: { effect?: string | null; p: SharedValue<number>; w: number; h: number }) {
  const fx = effect ? EFFECTS[effect] : null;
  const icon = useAnimatedStyle(() => ({ opacity: interpolate(p.value, [0, 0.2, 0.7, 1], [0, 0.9, 0.6, 0]), transform: [{ scale: interpolate(p.value, [0, 0.3, 1], [0.3, 1.25, 1.6]) }, { rotate: `${(fx?.motion === "swirlIn" || fx?.motion === "swirlOut" || fx?.motion === "spiral" ? p.value * 300 : 0)}deg` }] }));
  if (!fx) return null;
  return (
    <View pointerEvents="none" style={{ position: "absolute", alignItems: "center", justifyContent: "center", width: 1, height: 1 }}>
      <Animated.View style={[{ position: "absolute", width: 190, height: 190, borderRadius: 95, alignItems: "center", justifyContent: "center", backgroundColor: fx.c1 + "2E" }, icon]}>
        <Icon name={fx.icon as any} size={110} color={fx.c1} />
      </Animated.View>
      {Array.from({ length: N }, (_, i) => <Particle key={i} i={i} p={p} motion={fx.motion} color={i % 3 ? fx.c1 : fx.c2} w={w} h={h} />)}
    </View>
  );
}

// Small inline entry preview (shop cards / sheets). Plays sound on each replay.
export function EntryEffect({ effect, fromRight = false, children, play = 0, sound = false }: { effect?: string | null; fromRight?: boolean; children: React.ReactNode; play?: number; sound?: boolean }) {
  const reduced = useReducedMotion();
  const { width } = useWindowDimensions();
  const x = useSharedValue(0), s = useSharedValue(1), p = useSharedValue(0);
  useEffect(() => {
    if (sound && play) playSfx(effect);
    if (reduced) return;
    x.value = fromRight ? 200 : -200;
    s.value = 0.4;
    p.value = 0;
    x.value = withTiming(0, { duration: 650, easing: Easing.out(Easing.back(1.4)) });
    s.value = withDelay(150, withSpring(1, { damping: 9 }));
    p.value = effect ? withTiming(1, { duration: 1400, easing: Easing.out(Easing.quad) }) : 0;
  }, [effect, fromRight, reduced, play]); // eslint-disable-line react-hooks/exhaustive-deps
  const body = useAnimatedStyle(() => ({ transform: [{ translateX: x.value }, { scale: s.value }] }));
  return (
    <View style={{ alignItems: "center", justifyContent: "center" }}>
      <Burst effect={effect} p={p} w={Math.min(width, 360) * 0.7} h={170} />
      <Animated.View style={body}>{children}</Animated.View>
    </View>
  );
}

type P = { name?: string; avatar?: string | null; frame?: string | null; entry?: string | null; bot?: boolean };

// Full-screen 3-second duel intro: you blast in, rival blasts in, VS slam, FIGHT. Then card 1.
export function EntryShow({ me, opp, onDone, testID = "entry-show" }: { me?: P; opp?: P; onDone?: () => void; testID?: string }) {
  const { width: W, height: H } = useWindowDimensions();
  const reduced = useReducedMotion();
  const a = useSharedValue(0), b = useSharedValue(0), pa = useSharedValue(0), pb = useSharedValue(0);
  const vs = useSharedValue(0), flash = useSharedValue(0), shake = useSharedValue(0), out = useSharedValue(1), fight = useSharedValue(0);
  useEffect(() => {
    const ease = Easing.out(Easing.back(1.3));
    const timers = [
      setTimeout(() => playSfx(me?.entry || "entry_rocket"), 0),
      setTimeout(() => playSfx(opp?.entry || "entry_lightning", 0.85), 750),
      setTimeout(() => playSfx("vs"), 1500),
      setTimeout(() => playSfx("go", 0.8), 2250),
    ];
    if (reduced) {
      a.value = 1; b.value = 1; vs.value = 1; fight.value = 1;
      const t = setTimeout(() => onDone?.(), 3000);
      return () => { clearTimeout(t); timers.forEach(clearTimeout); };
    }
    a.value = withTiming(1, { duration: 700, easing: ease });
    pa.value = withTiming(1, { duration: 1300, easing: Easing.out(Easing.quad) });
    b.value = withDelay(750, withTiming(1, { duration: 700, easing: ease }));
    pb.value = withDelay(750, withTiming(1, { duration: 1300, easing: Easing.out(Easing.quad) }));
    vs.value = withDelay(1500, withSpring(1, { damping: 7, stiffness: 180 }));
    flash.value = withDelay(1500, withSequence(withTiming(0.85, { duration: 70 }), withTiming(0, { duration: 380 })));
    shake.value = withDelay(1500, withSequence(withTiming(10, { duration: 50 }), withTiming(-10, { duration: 50 }), withTiming(6, { duration: 50 }), withTiming(0, { duration: 60 })));
    fight.value = withDelay(2250, withSpring(1, { damping: 8 }));
    out.value = withDelay(2700, withTiming(0, { duration: 300 }, (f) => { if (f && onDone) runOnJS(onDone)(); }));
    return () => timers.forEach(clearTimeout);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const root = useAnimatedStyle(() => ({ opacity: out.value, transform: [{ translateX: shake.value }] }));
  const left = useAnimatedStyle(() => ({ transform: [{ translateX: interpolate(a.value, [0, 1], [-W, 0]) }, { scale: interpolate(a.value, [0, 1], [0.4, 1]) }] }));
  const right = useAnimatedStyle(() => ({ transform: [{ translateX: interpolate(b.value, [0, 1], [W, 0]) }, { scale: interpolate(b.value, [0, 1], [0.4, 1]) }] }));
  const vsS = useAnimatedStyle(() => ({ opacity: vs.value > 0.05 ? 1 : 0, transform: [{ scale: interpolate(vs.value, [0, 1], [4, 1]) }, { rotate: `${interpolate(vs.value, [0, 1], [-25, 0])}deg` }] }));
  const flashS = useAnimatedStyle(() => ({ opacity: flash.value }));
  const fightS = useAnimatedStyle(() => ({ opacity: fight.value, transform: [{ scale: interpolate(fight.value, [0, 1], [0.3, 1]) }] }));
  const size = Math.min(132, W * 0.32);

  const player = (p: P | undefined, mine: boolean) => (
    <View style={{ alignItems: "center", gap: 8, width: W * 0.42 }}>
      <Avatar icon={p?.avatar} frame={p?.frame} size={size} />
      <T w="heavy" size={17} color={colors.onSurfaceInverse} numberOfLines={1}>{mine ? "You" : p?.name || "Rival"}</T>
      {p?.bot ? <RivalTag /> : null}
      {p?.entry ? <T w="bold" size={11} color={EFFECTS[p.entry]?.c1 || colors.custom_gameMuted} numberOfLines={1}>{EFFECTS[p.entry] ? p.entry.replace("entry_", "").toUpperCase() + " ENTRY" : ""}</T> : null}
    </View>
  );

  return (
    <Animated.View testID={testID} style={[StyleSheet.absoluteFill, { zIndex: 50 }, root]}>
      <LinearGradient colors={[colors.custom_gameCardHi, colors.custom_gameBg, colors.custom_examJeeDeep]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
      <View style={{ flex: 1, justifyContent: "center", gap: H * 0.04 }}>
        <Animated.View style={[{ alignSelf: "flex-start", marginLeft: W * 0.06, alignItems: "center", justifyContent: "center" }, left]}>
          <Burst effect={me?.entry || "entry_rocket"} p={pa} w={W} h={H * 0.5} />
          {player(me, true)}
        </Animated.View>
        <Animated.View style={[{ alignSelf: "center" }, vsS]}>
          <LinearGradient colors={[colors.custom_neonAmber, colors.custom_examBitsat]} style={{ width: 92, height: 92, borderRadius: 46, alignItems: "center", justifyContent: "center", borderWidth: 3, borderColor: colors.onSurfaceInverse }}>
            <T w="heavy" size={38} color={colors.custom_gameBg}>VS</T>
          </LinearGradient>
        </Animated.View>
        <Animated.View style={[{ alignSelf: "flex-end", marginRight: W * 0.06, alignItems: "center", justifyContent: "center" }, right]}>
          <Burst effect={opp?.entry || "entry_lightning"} p={pb} w={W} h={H * 0.5} />
          {player(opp, false)}
        </Animated.View>
        <Animated.View style={[{ alignSelf: "center" }, fightS]}>
          <T w="heavy" size={46} color={colors.custom_neonAmber} style={{ letterSpacing: 4, textShadowColor: colors.custom_examBitsat, textShadowRadius: 16 }} testID="entry-fight">FIGHT!</T>
        </Animated.View>
      </View>
      <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFill, { backgroundColor: colors.onSurfaceInverse }, flashS]} />
    </Animated.View>
  );
}

export function RivalTag() {
  return (
    <View testID="duel-ai-rival-tag" style={{ flexDirection: "row", alignItems: "center", gap: 3, paddingHorizontal: 6, height: 20, borderRadius: 10, backgroundColor: colors.custom_neonCyan }}>
      <Icon name="robot" size={11} color={colors.custom_gameBg} />
      <T w="heavy" size={11} color={colors.custom_gameBg}>AI RIVAL</T>
    </View>
  );
}
