import React, { useEffect } from "react";
import { StyleSheet, View } from "react-native";
import Animated, { css, useReducedMotion } from "react-native-reanimated";
import { Image } from "expo-image";
import Svg, { Circle, Defs, Path, RadialGradient, Stop } from "react-native-svg";
import { T } from "@/src/components/ui";
import { firstToday, playSfx } from "@/src/sfx";
import { allIndia, arena } from "@/src/theme";
import { Alive } from "./Art";
import { Glitter } from "./Glitter";
import { Twinkles } from "./juice";
import { DUST, Fire, GALLOP, SPIN, run } from "./DailyScenes";

// Battleground Victory (top 100 in India): the riders charge in across the burning ridge, the lead rider holding the
// golden cup high, the student's own battleground raging behind. Drawn on a 360 × 240 stage, scaled to the width.
const SW = 360, SH = 240;
const ART = {
  trophy: require("../../assets/arena/daily_trophy.webp"),
  riders: [require("../../assets/arena/sil_rider1.webp"), require("../../assets/arena/sil_rider2.webp"), require("../../assets/arena/sil_rider3.webp")],
};
const CHARGE = css.keyframes({ from: { transform: [{ translateX: -420 }] }, to: { transform: [{ translateX: 0 }] } });
const SHOW = css.keyframes({ from: { opacity: 0, transform: [{ scale: 0.6 }] }, to: { opacity: 1, transform: [{ scale: 1 }] } });
const RIDERS = [ // back to front; the lead (last) carries the cup
  { src: ART.riders[2], size: 128, left: 232, top: 95, ms: 1500, delay: 260 },
  { src: ART.riders[1], size: 120, left: 8, top: 117, ms: 1700, delay: 120 },
  { src: ART.riders[0], size: 150, left: 105, top: 77, ms: 1350, delay: 0, cup: true },
];
const once = (still: boolean, name: object, ms: number, delay: number) => (still ? null : {
  animationName: name, animationDuration: ms, animationDelay: delay, animationTimingFunction: "ease-out" as const, animationFillMode: "backwards" as const,
});

function Rays() {
  const c = 110, n = 14;
  return <Svg width={220} height={220}>{Array.from({ length: n }, (_, i) => (i / n) * Math.PI * 2).map((a) => <Path key={a} fill={arena.gold} opacity={0.13}
    d={`M${c} ${c} L${c + Math.cos(a - 0.1) * c} ${c + Math.sin(a - 0.1) * c} L${c + Math.cos(a + 0.1) * c} ${c + Math.sin(a + 0.1) * c} Z`} />)}</Svg>;
}

export function BattleVictory({ width, rank }: { width: number; rank: number }) {
  const still = !!useReducedMotion(), inner = width - 5, k = inner / SW;
  useEffect(() => { // the gallop as they charge in, then the war horn and the crowd: heard once a day, not each time the result is opened
    let on = true, t: ReturnType<typeof setTimeout> | undefined;
    void firstToday("charge", () => on).then((first) => {
      if (!first) return;
      playSfx("scene_race", 0.8);
      t = setTimeout(() => playSfx("scene_cup", 0.9), 1100);
    });
    return () => { on = false; clearTimeout(t); };
  }, []);
  // The ring is exactly as wide as its picture (never stretched by a wide screen: an open Fold showed the ring's colours as a strip beside it).
  return <Glitter radius={24} ring={2.5} sparkles={4} style={{ width, alignSelf: "center" }} inner={{ width: inner, height: inner * (SH / SW), backgroundColor: arena.bgDeep }}>
    <View testID="rf-battle-victory" accessibilityLabel={`Battleground victory. Top 100 in India, rank ${rank}`} style={[styles.stage, { left: (inner - SW) / 2, top: (inner * (SH / SW) - SH) / 2, transform: [{ scale: k }] }]}>
      <Fire still={still} wind />
      <Animated.View style={[styles.rays, once(still, SHOW, 700, 1300), run(still, SPIN, 22000)]}><Rays /></Animated.View>
      {RIDERS.map((r, i) => <Animated.View key={i} style={[styles.abs, { left: r.left, top: r.top, width: r.size, height: r.size }, once(still, CHARGE, r.ms, r.delay)]}>
        {still ? null : [0, 1].map((d) => <Animated.View key={d} style={[styles.dust, { left: r.size * 0.04, top: r.size * 0.7 }, run(false, DUST, 600, { delay: d * 300 + r.delay })]} />)}
        <Animated.View style={[styles.full, run(still, GALLOP, 400, { delay: r.delay })]}>
          {r.cup ? <View style={styles.cup}>
            <Svg style={styles.cupGlow} width={130} height={130}>
              {/* a dark halo first so the gold cup stands out from the bright fire, then a thin gold glow */}
              <Defs><RadialGradient id="bvGlow" cx="50%" cy="50%" r="50%"><Stop offset="0" stopColor={allIndia.ink} stopOpacity={0.8} /><Stop offset="0.55" stopColor={allIndia.ink} stopOpacity={0.45} /><Stop offset="0.8" stopColor={arena.gold} stopOpacity={0.25} /><Stop offset="1" stopColor={arena.gold} stopOpacity={0} /></RadialGradient></Defs>
              <Circle cx={65} cy={65} r={65} fill="url(#bvGlow)" />
            </Svg>
            <Alive kind="float"><Image source={ART.trophy} contentFit="contain" style={styles.cupArt} accessible={false} /></Alive>
          </View> : null}
          <Image source={r.src} style={styles.full} contentFit="contain" />
        </Animated.View>
      </Animated.View>)}
      <Twinkles spots={[[44, 6, 12], [58, 14, 10], [36, 24, 9], [64, 30, 11]]} />
    </View>
    <View style={styles.badge}><T testID="rf-battle-victory-badge" w="heavy" size={11} color={arena.gold} style={styles.spaced}>TOP 100 · ALL INDIA</T></View>
  </Glitter>;
}

const styles = StyleSheet.create({
  stage: { position: "absolute", width: SW, height: SH, overflow: "hidden" },
  abs: { position: "absolute" }, full: { width: "100%", height: "100%" }, spaced: { letterSpacing: 1.6 },
  rays: { position: "absolute", left: 72, top: -40, width: 220, height: 220 },
  cup: { position: "absolute", left: 38, top: -58, width: 76, height: 76 },
  cupGlow: { position: "absolute", left: -27, top: -27 },
  cupArt: { width: 76, height: 76 },
  dust: { position: "absolute", width: 30, height: 30, borderRadius: 15, backgroundColor: allIndia.dust, opacity: 0 },
  badge: { position: "absolute", top: 10, left: 10, height: 28, paddingHorizontal: 10, borderRadius: 14, justifyContent: "center", backgroundColor: arena.scrim, borderWidth: 1, borderColor: arena.goldDeep },
});
