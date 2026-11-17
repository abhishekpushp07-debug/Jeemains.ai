// "Aapka impact" on the Mission tab: how many friends the student's link has brought to free education.
// Royal night blue with gold, like the card. A gold medal with the count (counts up once), the thank-you line,
// "+K is hafte", and a thin gold track to the next milestone. Zero shows an invitation, never a made-up number.
import React, { useEffect, useRef, useState } from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Animated, { FadeIn, useReducedMotion } from "react-native-reanimated";
import { T, Skeleton } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { colors as c } from "@/src/theme";
import { SERIF } from "@/src/rank/tones";
import { Glow } from "./parts";
import { MissionStats, nextStep, shortCount } from "./stats";

/** Counts from the last shown value up to n in ~0.9 s (JS timer, no worklet). Reduce Motion shows n at once. */
function useCountUp(n: number, reduced: boolean) {
  const shown = useRef(0);
  const [v, setV] = useState(reduced ? n : 0);
  useEffect(() => {
    const from = shown.current;
    if (reduced || n <= from) { shown.current = n; setV(n); return; }
    const t0 = Date.now();
    let raf = 0;
    const step = () => {
      const p = Math.min(1, (Date.now() - t0) / 900);
      const x = Math.round(from + (n - from) * (1 - Math.pow(1 - p, 3)));
      shown.current = x; setV(x);
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [n, reduced]);
  return v;
}

export function ImpactPanel({ stats, loading }: { stats: MissionStats | null; loading: boolean }) {
  const reduced = useReducedMotion();
  const helped = stats?.helped ?? 0;
  const shown = useCountUp(helped, reduced);
  if (loading) return <Skeleton h={128} style={{ borderRadius: 22 }} />;
  if (!stats) return null; // offline or not reachable: the share buttons stay, no panel
  const goal = nextStep(helped);
  const week = stats.week;
  return <Animated.View testID="mission-impact" entering={reduced ? undefined : FadeIn.duration(320)} style={s.panel}>
    <LinearGradient colors={[c.custom_mBlueMid, c.custom_mBlueTo, c.custom_mBlueNight]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    <Glow color={c.custom_mGold} cx="12%" cy="0%" r="70%" opacity={0.2} />
    <View style={s.row}>
      <View style={s.ring}>
        <LinearGradient colors={[c.custom_mGoldLight, c.custom_mGold, c.custom_mGoldDeep]} start={{ x: 0.2, y: 0 }} end={{ x: 0.8, y: 1 }} style={StyleSheet.absoluteFill} />
        <View style={s.medal}>
          {helped > 0
            ? <>
              <T testID="mission-impact-count" w="heavy" allowFontScaling={false} color={c.custom_mGold}
                style={{ fontFamily: SERIF, fontSize: shortCount(helped).length > 4 ? 19 : shortCount(helped).length > 2 ? 24 : 30, lineHeight: 34 }}>{shortCount(shown)}</T>
              <T w="heavy" size={8} allowFontScaling={false} color={c.custom_mInk} style={{ letterSpacing: 1.6, lineHeight: 10 }}>DOST</T>
            </>
            : <Glyph name="hand-heart" size={30} color={c.custom_mGold} />}
        </View>
      </View>
      <View style={{ flex: 1, gap: 4 }}>
        <T w="heavy" size={10.5} color={c.custom_mGold} style={{ letterSpacing: 2 }}>{helped > 0 ? "THANK YOU! 🙏" : "AAPKA IMPACT"}</T>
        {helped > 0
          ? <T testID="mission-impact-line" w="heavy" size={16} color={c.custom_mWhite} style={{ lineHeight: 21 }}>
            Aapne <T w="heavy" size={16} color={c.custom_mGold}>{shortCount(helped)} {helped === 1 ? "dost" : "logon"}</T> ki free education mein help ki
          </T>
          : <T testID="mission-impact-line" w="heavy" size={15.5} color={c.custom_mWhite} style={{ lineHeight: 21 }}>Aapka pehla share kisi ki free taiyari shuru karega</T>}
        {week > 0 ? <View testID="mission-impact-week" style={s.week}>
          <Glyph name="trending-up" size={13} color={c.custom_mGold} />
          <T w="heavy" size={11.5} color={c.custom_mGold}>+{shortCount(week)} is hafte</T>
        </View> : null}
      </View>
    </View>
    {helped > 0 ? <View style={{ gap: 6 }}>
      <View style={s.between}>
        <T w="semibold" size={12} color={c.custom_mInk}>Agla padaav: {shortCount(goal)} dost</T>
        <T testID="mission-impact-goal" w="heavy" size={12} color={c.custom_mGold}>{shortCount(helped)}/{shortCount(goal)}</T>
      </View>
      <View style={s.track}>
        <LinearGradient colors={[c.custom_mGoldDeep, c.custom_mGold, c.custom_mGoldLight]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
          style={{ width: `${Math.max(6, Math.min(100, (helped / goal) * 100))}%`, height: "100%", borderRadius: 3 }} />
      </View>
    </View> : null}
    <View style={s.rule} />
    <T testID="mission-impact-how" size={12} color={c.custom_mInkSoft} style={{ lineHeight: 17 }}>
      Jab koi dost aapke link se JEELIVE.AI kholta hai, wo yahan gina jaata hai. Har dost sirf ek baar.
    </T>
  </Animated.View>;
}

const s = StyleSheet.create({
  panel: { borderRadius: 22, padding: 16, gap: 14, overflow: "hidden", borderWidth: 1, borderColor: c.custom_mGoldLine, backgroundColor: c.custom_mBlueTo },
  row: { flexDirection: "row", alignItems: "center", gap: 14 },
  ring: { width: 76, height: 76, borderRadius: 38, padding: 2.5, overflow: "hidden" },
  medal: { flex: 1, borderRadius: 36, alignItems: "center", justifyContent: "center", backgroundColor: c.custom_mBlueNight },
  week: { flexDirection: "row", alignItems: "center", gap: 4, alignSelf: "flex-start", marginTop: 2, paddingHorizontal: 9, paddingVertical: 4,
    borderRadius: 999, backgroundColor: c.custom_mGoldWash, borderWidth: 1, borderColor: c.custom_mGoldLine },
  between: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  track: { height: 6, borderRadius: 3, overflow: "hidden", backgroundColor: c.custom_mGlass },
  rule: { height: 1, backgroundColor: c.custom_mLine },
});
