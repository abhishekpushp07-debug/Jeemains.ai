import React from "react";
import { StyleSheet, View } from "react-native";
import Animated, { css } from "react-native-reanimated";
import { Image } from "expo-image";
import Svg, { Circle, Defs, Ellipse, Line, LinearGradient as SvgGradient, Path, RadialGradient, Stop } from "react-native-svg";
import { T } from "@/src/components/ui";
import { allIndia, arena, fx } from "@/src/theme";
import { Alive } from "./Art";
import { Twinkles, rnd } from "./juice";
import type { DailyLook } from "./daily";

// The five All India card scenes share one world (the student's pick): a dark ridge against blazing red smoke, the
// student's own battleground (riders in the smoke) on the horizon, black silhouettes in front and embers rising. Every scene is drawn on a 360 × 360 stage, then scaled to the card.
// Motion is CSS animation (UI thread on phones, plain CSS on the web); with Reduce Motion each scene rests in its best pose.
const B = 360;

const ART = {
  fire: require("../../assets/arena/th_fire_bg.webp"), ship: require("../../assets/arena/sil_ship.webp"), battle: require("../../assets/arena/battleground.webp"),
  trophy: require("../../assets/arena/daily_trophy.webp"), lion: require("../../assets/arena/sil_lion.webp"), archer: require("../../assets/arena/sil_archer.webp"),
  riders: [require("../../assets/arena/sil_rider1.webp"), require("../../assets/arena/sil_rider2.webp"), require("../../assets/arena/sil_rider3.webp")],
};

type Ease = "linear" | "ease-in-out" | "ease-out" | "ease-in";
const run = (still: boolean, name: any, ms: number, o: { delay?: number; ease?: Ease; alt?: boolean } = {}) => (still ? null : {
  animationName: name, animationDuration: ms, animationDelay: o.delay || 0, animationIterationCount: "infinite" as const,
  animationTimingFunction: o.ease || "linear", animationDirection: o.alt ? ("alternate" as const) : ("normal" as const),
});
const at = (x: number, y: number, r = 0, s = 1) => ({ transform: [{ translateX: x }, { translateY: y }, { rotate: `${r}deg` }, { scale: s }] });

// ---- The fire world: smoke slowly drifting, the glow breathing, embers rising off the ridge (or blown sideways by the race).
const DRIFT = css.keyframes({ from: { transform: [{ scale: 1 }, { translateX: 0 }] }, to: { transform: [{ scale: 1.07 }, { translateX: -8 }] } });
const PARALLAX = css.keyframes({ from: { transform: [{ translateX: -4 }] }, to: { transform: [{ translateX: 6 }] } });
const FLARE = css.keyframes({ from: { opacity: 0.3, transform: [{ scale: 0.92 }] }, to: { opacity: 0.75, transform: [{ scale: 1.06 }] } });
const RISE = css.keyframes({
  "0%": { opacity: 0, ...at(0, 0) }, "15%": { opacity: 1, ...at(6, -30) }, "60%": { opacity: 0.85, ...at(-8, -120, 0, 0.8) }, "100%": { opacity: 0, ...at(10, -200, 0, 0.4) },
});
const WIND = css.keyframes({ "0%": { opacity: 0, ...at(0, 0) }, "15%": { opacity: 0.9, ...at(-60, -3) }, "100%": { opacity: 0, ...at(-440, -22) } });
const EMBERS = Array.from({ length: 14 }, (_, i) => ({ x: 10 + rnd(i, 1) * 340, y: 182 + rnd(i, 2) * 30, s: 3 + rnd(i, 3) * 3.5, ms: 2600 + rnd(i, 4) * 2400, delay: rnd(i, 5) * 3000, c: [allIndia.ember, allIndia.flame, arena.gold][i % 3] }));

function Fire({ still, wind }: { still: boolean; wind?: boolean }) {
  return <>
    <Animated.View style={[styles.bg, run(still, DRIFT, 9000, { ease: "ease-in-out", alt: true })]}><Image source={ART.fire} style={styles.full} contentFit="cover" /></Animated.View>
    <Animated.View style={[styles.flare, run(still, FLARE, 2600, { ease: "ease-in-out", alt: true })]}>
      <Svg width={340} height={240}>
        <Defs><RadialGradient id="aiFlare" cx="50%" cy="50%" r="50%"><Stop offset="0" stopColor={allIndia.hot} stopOpacity={0.85} /><Stop offset="0.45" stopColor={allIndia.flame} stopOpacity={0.4} /><Stop offset="1" stopColor={allIndia.flame} stopOpacity={0} /></RadialGradient></Defs>
        <Ellipse cx={170} cy={120} rx={170} ry={120} fill="url(#aiFlare)" />
      </Svg>
    </Animated.View>
    <Animated.View style={[styles.battle, run(still, PARALLAX, 9000, { ease: "ease-in-out", alt: true })]}><Image source={ART.battle} style={styles.full} contentFit="fill" /></Animated.View>
    {still ? null : EMBERS.map((e, i) => <Animated.View key={i} style={[styles.ember, wind
      ? { left: 360 + e.x * 0.2, top: 40 + rnd(i, 6) * 170, width: e.s * 5, height: 2, backgroundColor: e.c }
      : { left: e.x, top: e.y, width: e.s, height: e.s, borderRadius: e.s, backgroundColor: e.c },
      run(false, wind ? WIND : RISE, wind ? e.ms * 0.32 : e.ms, { delay: wind ? e.delay * 0.3 : e.delay, ease: wind ? "linear" : "ease-out" })]} />)}
  </>;
}

// ---- 1 · Space Race: a rocket blasts out of the fire, hovers over the ridge, and rockets off into the night.
const TILT = -24;
const FLY = css.keyframes({
  "0%": { opacity: 0, ...at(-260, 118, 0, 0.6) }, "6%": { opacity: 1, ...at(-230, 104, 0, 0.66) }, "38%": { opacity: 1, ...at(0, 0) },
  "66%": { opacity: 1, ...at(14, -6, 0, 1.02) }, "94%": { opacity: 1, ...at(280, -124, 0, 0.7) }, "100%": { opacity: 0, ...at(310, -138, 0, 0.6) },
});
const FLICKER = css.keyframes({ from: { opacity: 0.75, transform: [{ scaleX: 0.8 }, { scaleY: 0.88 }] }, to: { opacity: 1, transform: [{ scaleX: 1.15 }, { scaleY: 1.06 }] } });
const STREAK = css.keyframes({ "0%": { opacity: 0, ...at(0, 0, TILT) }, "20%": { opacity: 0.8, ...at(-80, 36, TILT) }, "100%": { opacity: 0, ...at(-384, 171, TILT) } });
const STREAKS = Array.from({ length: 10 }, (_, i) => ({ x: 170 + rnd(i, 7) * 300, y: -20 + rnd(i, 8) * 200, w: 36 + rnd(i, 9) * 50, ms: 700 + rnd(i, 10) * 600, delay: rnd(i, 11) * 1400 }));

function Space({ still }: { still: boolean }) {
  return <>
    <Twinkles color={allIndia.star} spots={[[8, 9, 9], [22, 5, 6], [78, 7, 8], [92, 17, 10], [60, 3, 6], [38, 11, 5], [6, 28, 6]]} />
    {still ? null : STREAKS.map((s, i) => <Animated.View key={i} style={[styles.streak, { left: s.x, top: s.y, width: s.w }, run(false, STREAK, s.ms, { delay: s.delay })]} />)}
    <Animated.View style={[styles.ship, run(still, FLY, 5200, { ease: "ease-in-out" })]}>
      <View style={styles.shipTilt}>
        <Animated.View style={[styles.flame, run(still, FLICKER, 120, { alt: true })]}>
          <Svg width={110} height={30}>
            <Defs><SvgGradient id="aiFlame" x1="1" y1="0" x2="0" y2="0"><Stop offset="0" stopColor={allIndia.hot} /><Stop offset="0.35" stopColor={allIndia.ember} /><Stop offset="0.7" stopColor={allIndia.flame} stopOpacity={0.7} /><Stop offset="1" stopColor={allIndia.flame} stopOpacity={0} /></SvgGradient></Defs>
            <Path d="M110 15 C80 1 34 5 0 15 C34 25 80 29 110 15 Z" fill="url(#aiFlame)" />
            <Path d="M110 15 C92 9 70 10 58 15 C70 20 92 21 110 15 Z" fill={fx.white} opacity={0.9} />
          </Svg>
        </Animated.View>
        <Image source={ART.ship} style={styles.full} contentFit="contain" />
      </View>
    </Animated.View>
  </>;
}

// ---- 2 · World Cup: the golden cup blazing over the student's battleground, gold light turning behind it.
const SPIN = css.keyframes({ from: { transform: [{ rotate: "0deg" }] }, to: { transform: [{ rotate: "360deg" }] } });

function Rays({ still }: { still: boolean }) {
  const c = 200, n = 16;
  return <Animated.View style={[styles.rays, run(still, SPIN, 26000)]}>
    <Svg width={400} height={400}>{Array.from({ length: n }, (_, i) => (i / n) * Math.PI * 2).map((a) => <Path key={a} fill={arena.gold} opacity={0.2}
      d={`M${c} ${c} L${c + Math.cos(a - 0.09) * c} ${c + Math.sin(a - 0.09) * c} L${c + Math.cos(a + 0.09) * c} ${c + Math.sin(a + 0.09) * c} Z`} />)}</Svg>
  </Animated.View>;
}

function Cup({ still }: { still: boolean }) {
  return <>
    <Rays still={still} />
    <Svg style={styles.cupGlow} width={240} height={240}>
      <Defs><RadialGradient id="aiCupGlow" cx="50%" cy="50%" r="50%"><Stop offset="0" stopColor={arena.gold} stopOpacity={0.6} /><Stop offset="1" stopColor={arena.gold} stopOpacity={0} /></RadialGradient></Defs>
      <Circle cx={120} cy={120} r={120} fill="url(#aiCupGlow)" />
    </Svg>
    <View style={styles.trophy}>
      <Alive kind="float"><Image source={ART.trophy} contentFit="contain" style={styles.cupArt} accessible={false} /></Alive>
      <Twinkles spots={[[16, 18, 14], [86, 24, 12], [50, 0, 11], [24, 70, 10], [80, 64, 12]]} />
    </View>
  </>;
}

// ---- 3 · Lion Clash: two lions crouch, leap and crash into each other in a white-hot burst.
const LUNGE = css.keyframes({
  "0%": at(-30, 0), "36%": at(-40, 5, 4), "52%": at(16, -18, -8), "58%": at(8, -6, -3), "80%": at(-22, 0), "100%": at(-30, 0),
});
const CLASH = css.keyframes({
  "0%": { opacity: 0, transform: [{ scale: 0.2 }] }, "48%": { opacity: 0, transform: [{ scale: 0.2 }] }, "53%": { opacity: 1, transform: [{ scale: 1.15 }] },
  "68%": { opacity: 0, transform: [{ scale: 1.7 }] }, "100%": { opacity: 0, transform: [{ scale: 1.7 }] },
});
const SHAKE = css.keyframes({ "0%": at(0, 0), "50%": at(0, 0), "53%": at(4, -3), "56%": at(-4, 2), "59%": at(3, -1), "62%": at(0, 0), "100%": at(0, 0) });
const BEAT = css.keyframes({ from: { transform: [{ scale: 1 }] }, to: { transform: [{ scale: 1.12 }] } });
const BURST = Array.from({ length: 24 }, (_, i) => { const a = (i / 24) * Math.PI * 2, r = i % 2 ? 26 : 70; return `${70 + Math.cos(a) * r} ${70 + Math.sin(a) * r}`; }).join(" L");
const CLASH_MS = 2600;

function Lion({ side, still }: { side: "left" | "right"; still: boolean }) {
  return <View style={[styles.lion, side === "right" && styles.lionRight]}>
    <Animated.View style={[styles.full, still ? at(-14, 0) : null, run(still, LUNGE, CLASH_MS, { ease: "ease-in-out" })]}><Image source={ART.lion} style={styles.full} contentFit="contain" /></Animated.View>
  </View>;
}

function Lions({ still }: { still: boolean }) {
  return <Animated.View style={[StyleSheet.absoluteFill, run(still, SHAKE, CLASH_MS)]}>
    <Lion side="left" still={still} />
    <Lion side="right" still={still} />
    {still ? null : <Animated.View style={[styles.burst, run(false, CLASH, CLASH_MS)]}>
      <Svg width={140} height={140}>
        <Defs><RadialGradient id="aiBurst" cx="50%" cy="50%" r="50%"><Stop offset="0" stopColor={fx.white} /><Stop offset="0.5" stopColor={allIndia.hot} /><Stop offset="1" stopColor={allIndia.ember} stopOpacity={0.2} /></RadialGradient></Defs>
        <Path d={`M${BURST} Z`} fill="url(#aiBurst)" />
      </Svg>
    </Animated.View>}
    <Animated.View style={[styles.vs, run(still, BEAT, 650, { ease: "ease-in-out", alt: true })]}><T w="heavy" size={17} color={arena.badgeInk}>VS</T></Animated.View>
  </Animated.View>;
}

// ---- 4 · Cavalry Race: three riders thunder along the burning ridge, swapping the lead, dust flying, embers blown back.
const JOSTLE = css.keyframes({ from: { transform: [{ translateX: -22 }] }, to: { transform: [{ translateX: 26 }] } });
const GALLOP = css.keyframes({ "0%": at(0, 0), "50%": at(0, -8, -3), "100%": at(0, 0) });
const DUST = css.keyframes({ from: { opacity: 0.8, ...at(0, 0, 0, 0.5) }, to: { opacity: 0, ...at(-64, -12, 0, 1.8) } });
const RIDERS = [
  { src: ART.riders[1], size: 118, left: 204, top: 121, jostle: 3100, delay: 0 },
  { src: ART.riders[2], size: 138, left: 106, top: 88, jostle: 2500, delay: 140 },
  { src: ART.riders[0], size: 158, left: 12, top: 78, jostle: 3700, delay: 260 },
];

function Race({ still }: { still: boolean }) {
  return <>{RIDERS.map((r, i) => <Animated.View key={i} style={[styles.abs, { left: r.left, top: r.top, width: r.size, height: r.size }, run(still, JOSTLE, r.jostle, { ease: "ease-in-out", alt: true })]}>
    {still ? null : [0, 1].map((k) => <Animated.View key={k} style={[styles.dust, { left: r.size * 0.06, top: r.size * 0.7 }, run(false, DUST, 640, { delay: k * 320 + r.delay })]} />)}
    <Animated.View style={[styles.full, run(still, GALLOP, 420, { delay: r.delay })]}><Image source={r.src} style={styles.full} contentFit="contain" /></Animated.View>
  </Animated.View>)}</>;
}

// ---- 5 · Bullseye: the archer looses, the arrow streaks across the fire and thuds into the gold. +10.
const SHOT_MS = 2800, TX = 292, TY = 96, ARROW = 84;
const SHOOT = css.keyframes({
  "0%": { opacity: 0, ...at(-128, 0) }, "8%": { opacity: 1, ...at(-128, 0) }, "20%": { opacity: 1, ...at(-128, 0) }, "32%": { opacity: 1, ...at(0, 0) },
  "35%": { opacity: 1, ...at(0, 0, 4) }, "38%": { opacity: 1, ...at(0, 0, -3) }, "41%": { opacity: 1, ...at(0, 0, 1.5) }, "44%": { opacity: 1, ...at(0, 0) },
  "82%": { opacity: 1, ...at(0, 0) }, "92%": { opacity: 0, ...at(0, 0) }, "100%": { opacity: 0, ...at(0, 0) },
});
const TRAIL = css.keyframes({ "0%": { opacity: 0 }, "20%": { opacity: 0 }, "27%": { opacity: 1 }, "36%": { opacity: 0 }, "100%": { opacity: 0 } });
const THUD = css.keyframes({ "0%": { transform: [{ scale: 1 }] }, "31%": { transform: [{ scale: 1 }] }, "34%": { transform: [{ scale: 0.93 }] }, "38%": { transform: [{ scale: 1.04 }] }, "42%": { transform: [{ scale: 1 }] }, "100%": { transform: [{ scale: 1 }] } });
const RING = css.keyframes({ "0%": { opacity: 0, transform: [{ scale: 0.5 }] }, "31%": { opacity: 0, transform: [{ scale: 0.5 }] }, "33%": { opacity: 1, transform: [{ scale: 0.7 }] }, "56%": { opacity: 0, transform: [{ scale: 3.2 }] }, "100%": { opacity: 0, transform: [{ scale: 3.2 }] } });
const PLUS = css.keyframes({ "0%": { opacity: 0, ...at(0, 0, 0, 0.6) }, "32%": { opacity: 0, ...at(0, 0, 0, 0.6) }, "36%": { opacity: 1, ...at(0, -6, 0, 1.15) }, "62%": { opacity: 0, ...at(0, -36) }, "100%": { opacity: 0, ...at(0, -36) } });

function Target() {
  return <Svg width={130} height={190}>
    <Defs><RadialGradient id="aiTarget" cx="50%" cy="50%" r="50%"><Stop offset="0" stopColor={allIndia.flame} stopOpacity={0.55} /><Stop offset="1" stopColor={allIndia.flame} stopOpacity={0} /></RadialGradient></Defs>
    <Line x1={45} y1={90} x2={30} y2={186} stroke={allIndia.ink} strokeWidth={6} strokeLinecap="round" />
    <Line x1={85} y1={90} x2={100} y2={186} stroke={allIndia.ink} strokeWidth={6} strokeLinecap="round" />
    <Circle cx={65} cy={65} r={64} fill="url(#aiTarget)" />
    <Circle cx={65} cy={65} r={47} fill={allIndia.ink} stroke={arena.gold} strokeWidth={2} />
    {[38, 29, 20].map((r, i) => <Circle key={r} cx={65} cy={65} r={r} fill="none" stroke={i % 2 ? arena.gold : allIndia.flame} strokeWidth={3} />)}
    <Circle cx={65} cy={65} r={10} fill={allIndia.hot} stroke={arena.gold} strokeWidth={2.5} />
  </Svg>;
}

function Arrow() {
  return <Svg width={ARROW} height={16}>
    <Path d="M2 2 L20 8 L2 14 L9 8 Z" fill={fx.crimson} />
    <Line x1={6} y1={8} x2={72} y2={8} stroke={allIndia.ink} strokeWidth={3.5} strokeLinecap="round" />
    <Path d={`M70 3 L${ARROW} 8 L70 13 Z`} fill={allIndia.hot} />
  </Svg>;
}

function Archery({ still }: { still: boolean }) {
  return <>
    <Image source={ART.archer} style={styles.archer} contentFit="contain" />
    <Animated.View style={[styles.target, run(still, THUD, SHOT_MS)]}><Target /></Animated.View>
    {still ? null : <>
      <Animated.View style={[styles.trail, run(false, TRAIL, SHOT_MS)]}>
        <Svg width={128} height={4}><Defs><SvgGradient id="aiTrail" x1="0" y1="0" x2="1" y2="0"><Stop offset="0" stopColor={allIndia.flame} stopOpacity={0} /><Stop offset="1" stopColor={allIndia.hot} /></SvgGradient></Defs><Path d="M0 2 L128 0 L128 4 Z" fill="url(#aiTrail)" /></Svg>
      </Animated.View>
      <Animated.View style={[styles.ring, run(false, RING, SHOT_MS)]} />
      <Animated.View style={[styles.plus, run(false, PLUS, SHOT_MS)]}><T w="heavy" size={26} color={arena.gold} style={styles.plusText}>+10</T></Animated.View>
    </>}
    <Animated.View style={[styles.arrow, run(still, SHOOT, SHOT_MS)]}><Arrow /></Animated.View>
  </>;
}

const SCENES: Record<DailyLook, (p: { still: boolean }) => React.ReactElement> = { 1: Space, 2: Cup, 3: Lions, 4: Race, 5: Archery };
/** Each scene's short sound: launch, war horn + cheering crowd, roar, neigh + gallop, arrow whoosh + thud. */
export const SCENE_SOUND: Record<DailyLook, string> = { 1: "scene_space", 2: "scene_cup", 3: "scene_lion", 4: "scene_race", 5: "scene_arrow" };

/** The living picture behind the All India card: the fire world plus the chosen look's story. `size` = the card's inner side. */
export function DailyScene({ look, size, still }: { look: DailyLook; size: number; still: boolean }) {
  const Scene = SCENES[look];
  return <View pointerEvents="none" style={[styles.stage, { left: (size - B) / 2, top: (size - B) / 2, transform: [{ scale: size / B }] }]}>
    <Fire still={still} wind={look === 4} />
    <Scene still={still} />
  </View>;
}

const styles = StyleSheet.create({
  stage: { position: "absolute", width: B, height: B, overflow: "hidden", backgroundColor: allIndia.ink },
  abs: { position: "absolute" }, full: { width: "100%", height: "100%" },
  // The ridge of the fire picture sits at y ≈ 205, where every figure stands.
  bg: { position: "absolute", left: -30, top: -85, width: 420, height: 420 },
  flare: { position: "absolute", left: 10, top: 50 },
  battle: { position: "absolute", left: -20, top: 95, width: 400, height: 140 },
  ember: { position: "absolute", opacity: 0 },
  streak: { position: "absolute", height: 2, borderRadius: 1, backgroundColor: allIndia.star, opacity: 0 },
  ship: { position: "absolute", left: 75, top: 6, width: 210, height: 210 },
  shipTilt: { width: "100%", height: "100%", transform: [{ rotate: `${TILT}deg` }] },
  flame: { position: "absolute", left: -100, top: 90, width: 110, height: 30, transformOrigin: "100% 50%" },
  rays: { position: "absolute", left: -20, top: -88, width: 400, height: 400 },
  cupGlow: { position: "absolute", left: 60, top: -8 },
  trophy: { position: "absolute", left: 97, top: 28, width: 166, height: 166 }, cupArt: { width: 166, height: 166 },
  lion: { position: "absolute", left: -8, top: 63, width: 190, height: 190 },
  lionRight: { left: 178, transform: [{ scaleX: -1 }] },
  burst: { position: "absolute", left: 110, top: 62, width: 140, height: 140 },
  vs: { position: "absolute", left: 158, top: 52, width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: arena.gold, borderWidth: 2, borderColor: arena.goldDeep },
  dust: { position: "absolute", width: 30, height: 30, borderRadius: 15, backgroundColor: allIndia.dust, opacity: 0 },
  archer: { position: "absolute", left: -6, top: 36, width: 175, height: 175 },
  target: { position: "absolute", left: TX - 65, top: TY - 65, width: 130, height: 190 },
  arrow: { position: "absolute", left: TX - ARROW, top: TY - 8, width: ARROW, height: 16, transformOrigin: "100% 50%" },
  trail: { position: "absolute", left: TX - 128, top: TY - 2, width: 128, height: 4, opacity: 0 },
  ring: { position: "absolute", left: TX - 14, top: TY - 14, width: 28, height: 28, borderRadius: 14, borderWidth: 3, borderColor: arena.gold, opacity: 0 },
  plus: { position: "absolute", left: TX - 30, top: TY - 70, width: 60, alignItems: "center", opacity: 0 },
  plusText: { textShadowColor: allIndia.flame, textShadowRadius: 10, textShadowOffset: { width: 0, height: 0 } },
});
