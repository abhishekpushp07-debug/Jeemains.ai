import React, { useEffect } from "react";
import { ImageStyle, StyleProp, View } from "react-native";
import { Image } from "expo-image";
import Animated, { Easing, cancelAnimation, useAnimatedStyle, useReducedMotion, useSharedValue, withDelay, withRepeat, withSequence, withSpring, withTiming } from "react-native-reanimated";
import { arena } from "@/src/theme";
import { useStill } from "@/src/motion";

// Original arena artwork, bundled with the app (made once with tools/make_arena_art.py). Each picture carries its own glow.
const ICONS = {
  home: require("../../assets/arena/ic_home.webp"), trophy: require("../../assets/arena/ic_trophy.webp"), gang: require("../../assets/arena/ic_gang.webp"),
  store: require("../../assets/arena/ic_store.webp"), swords: require("../../assets/arena/ic_swords.webp"), friends: require("../../assets/arena/ic_friends.webp"),
  rival: require("../../assets/arena/ic_rival.webp"), bolt: require("../../assets/arena/ic_bolt.webp"), coin: require("../../assets/arena/ic_coin.webp"),
  flame: require("../../assets/arena/ic_flame.webp"), chest: require("../../assets/arena/ic_chest.webp"), target: require("../../assets/arena/ic_target.webp"),
  history: require("../../assets/arena/ic_history.webp"), back: require("../../assets/arena/ic_back.webp"),
};
export type GameIconName = keyof typeof ICONS;
// The Phoenix Diamond is built from layers: one fire wing (mirrored for the other side) and an upright diamond in the middle.
const WING_RATIO = 1.367; // height / width of one wing
const CENTRE_RATIO = 0.796; // height / width of the centre diamond

export const GEM_ORDER = ["red", "blue", "emerald", "gold", "kohinoor"] as const;
export type GemColor = (typeof GEM_ORDER)[number];
export const GEM_AT: Record<GemColor, number> = { red: 3, blue: 5, emerald: 10, gold: 15, kohinoor: 20 };
export const GEM_LABEL: Record<GemColor, string> = { red: "Red", blue: "Blue", emerald: "Emerald", gold: "Gold", kohinoor: "Kohinoor" };
const GEMS: Record<GemColor, number> = {
  red: require("../../assets/arena/gem_red.webp"), blue: require("../../assets/arena/gem_blue.webp"), emerald: require("../../assets/arena/gem_emerald.webp"),
  gold: require("../../assets/arena/gem_gold.webp"), kohinoor: require("../../assets/arena/gem_kohinoor.webp"),
};
const CENTRES: Record<GemColor, number> = {
  red: require("../../assets/arena/pgem_red.webp"), blue: require("../../assets/arena/pgem_blue.webp"), emerald: require("../../assets/arena/pgem_emerald.webp"),
  gold: require("../../assets/arena/pgem_gold.webp"), kohinoor: require("../../assets/arena/pgem_kohinoor.webp"),
};
// One wing picture per diamond colour (recoloured from the fire wing by tools/make_phoenix_wings.py).
const WINGS: Record<GemColor, number> = {
  red: require("../../assets/arena/phoenix_wing.webp"), blue: require("../../assets/arena/pwing_blue.webp"), emerald: require("../../assets/arena/pwing_emerald.webp"),
  gold: require("../../assets/arena/pwing_gold.webp"), kohinoor: require("../../assets/arena/pwing_kohinoor.webp"),
};
/** The rarest diamond a player owns: their Phoenix wears that colour. Red until the first diamond is won. */
export const topGem = (diamonds?: Record<string, number> | null): GemColor => [...GEM_ORDER].reverse().find((c) => (diamonds?.[c] || 0) > 0) || "red";
export const EMBLEM_IDS = ["lion", "eagle", "thunder", "crown", "shield", "dragon", "wolf", "rocket"] as const;
const EMBLEMS: Record<string, number> = {
  lion: require("../../assets/arena/em_lion.webp"), eagle: require("../../assets/arena/em_eagle.webp"), thunder: require("../../assets/arena/em_thunder.webp"),
  crown: require("../../assets/arena/em_crown.webp"), shield: require("../../assets/arena/em_shield.webp"), dragon: require("../../assets/arena/em_dragon.webp"),
  wolf: require("../../assets/arena/em_wolf.webp"), rocket: require("../../assets/arena/em_rocket.webp"),
};

/** Gentle life for artwork: a slow float, or a breathing pulse. Still when Reduce Motion is on. */
export function Alive({ children, kind = "float", delay = 0, style, once }: { children: React.ReactNode; kind?: "float" | "breathe" | "wiggle" | "hop"; delay?: number; style?: StyleProp<ImageStyle>; once?: boolean }) {
  const reduced = useStill();
  const t = useSharedValue(0);
  useEffect(() => {
    if (reduced) return;
    t.value = 0; // a loop always starts from rest, also when it resumes after the screen was covered
    const calm = Easing.inOut(Easing.sin), rest = withDelay(2600, withTiming(0, { duration: 0 }));
    // float and breathe never stop; wiggle and hop are a quick burst of fun, then a rest. `once`: one burst, then still.
    const loop = kind === "wiggle" ? withSequence(withTiming(1, { duration: 110 }), withTiming(-1, { duration: 170 }), withTiming(0.6, { duration: 140 }), withTiming(0, { duration: 120 }), rest)
      : kind === "hop" ? withSequence(withTiming(1, { duration: 240, easing: Easing.out(Easing.quad) }), withTiming(0, { duration: 420, easing: Easing.bounce }), rest)
      : withSequence(withTiming(1, { duration: 1500, easing: calm }), withTiming(0, { duration: 1500, easing: calm }));
    t.value = withDelay(delay, once && (kind === "wiggle" || kind === "hop") ? loop : withRepeat(loop, -1, false));
    return () => cancelAnimation(t);
  }, [reduced, t, delay, kind, once]);
  const a = useAnimatedStyle(() => (kind === "float" ? { transform: [{ translateY: -3 * t.value }, { rotate: `${-2 + 4 * t.value}deg` }] }
    : kind === "breathe" ? { transform: [{ scale: 1 + 0.05 * t.value }] }
    : kind === "wiggle" ? { transform: [{ rotate: `${t.value * 10}deg` }] }
    : { transform: [{ translateY: -10 * t.value }, { scaleY: 1 + 0.07 * t.value }] }));
  return <Animated.View style={[a, style as any]}>{children}</Animated.View>;
}

export function GameIcon({ name, size = 40, testID, style }: { name: GameIconName; size?: number; testID?: string; style?: StyleProp<ImageStyle> }) {
  return <Image testID={testID} source={ICONS[name]} contentFit="contain" accessible={false} style={[{ width: size, height: size }, style]} />;
}

/** One of the five streak diamonds. `locked` shows only its dark shape; `dim` is the unlit state before a milestone. */
export function Gem({ color, size = 40, locked, dim, testID }: { color: GemColor; size?: number; locked?: boolean; dim?: boolean; testID?: string }) {
  return <Image testID={testID} source={GEMS[color]} contentFit="contain" accessible={false} tintColor={locked ? arena.rim : undefined}
    style={{ width: size, height: size, opacity: locked ? 0.55 : dim ? 0.38 : 1 }} />;
}

export function Emblem({ id, size = 48, testID }: { id?: string | null; size?: number; testID?: string }) {
  return <Image testID={testID} source={EMBLEMS[id || ""] || EMBLEMS.lion} contentFit="contain" accessible={false} style={{ width: size, height: size }} />;
}

/**
 * The arena's mark: an upright diamond in the middle with a wing of fire on each side. Both wings are the same picture,
 * so the two sides always match. `breathe` lets the wings beat slowly and the diamond pulse; `burst` throws the wings open once.
 */
export function PhoenixDiamond({ width = 220, color = "red", breathe, burst, wingsOnly, testID }: { width?: number; color?: GemColor; breathe?: boolean; burst?: boolean; wingsOnly?: boolean; testID?: string }) {
  const reduced = useReducedMotion(), still = useStill();
  const beat = useSharedValue(0.5), open = useSharedValue(burst && !reduced ? 0 : 1);
  useEffect(() => {
    if (still) return;
    if (burst) open.value = withDelay(120, withSpring(1, { damping: 8, stiffness: 110 }));
    if (breathe) {
      const calm = Easing.inOut(Easing.sin);
      beat.value = 0.5;
      beat.value = withRepeat(withSequence(withTiming(1, { duration: 1300, easing: calm }), withTiming(0, { duration: 1300, easing: calm })), -1, false);
    }
    return () => { cancelAnimation(beat); cancelAnimation(open); };
  }, [still, breathe, burst, beat, open]);
  const half = width / 2, height = half * WING_RATIO, centre = width * 0.44;
  // Folded wings point straight up behind the diamond; open wings beat a few degrees around their root.
  const leftWing = useAnimatedStyle(() => ({ opacity: Math.min(1, open.value * 1.6), transform: [{ rotate: `${58 * (1 - open.value) + (beat.value - 0.5) * 7}deg` }, { scale: 0.55 + 0.45 * open.value }] }));
  const rightWing = useAnimatedStyle(() => ({ opacity: Math.min(1, open.value * 1.6), transform: [{ rotate: `${-58 * (1 - open.value) - (beat.value - 0.5) * 7}deg` }, { scale: 0.55 + 0.45 * open.value }] }));
  const gem = useAnimatedStyle(() => ({ transform: [{ scale: 1 + 0.05 * beat.value }] }));
  const wing = { width: half, height };
  // The wings always wear the colour of the diamond they carry.
  const art = WINGS[color];
  return <View testID={testID} accessible={false} style={{ width, height }}>
    <Animated.View style={[{ position: "absolute", left: 0, top: 0, transformOrigin: "100% 76%" }, wing, leftWing]}><Image source={art} contentFit="fill" style={wing} /></Animated.View>
    <Animated.View style={[{ position: "absolute", left: half, top: 0, transformOrigin: "0% 76%" }, wing, rightWing]}><Image source={art} contentFit="fill" style={[wing, { transform: [{ scaleX: -1 }] }]} /></Animated.View>
    {wingsOnly ? null : <Animated.View style={[{ position: "absolute", left: (width - centre) / 2, top: height * 0.27 }, gem]}>
      <Image testID={testID ? `${testID}-gem` : undefined} source={CENTRES[color]} contentFit="fill" style={{ width: centre, height: centre * CENTRE_RATIO }} />
    </Animated.View>}
  </View>;
}
