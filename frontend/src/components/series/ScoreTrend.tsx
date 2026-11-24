import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import Svg, { Circle, Defs, Line, LinearGradient, Path, Polyline, Rect, Stop } from "react-native-svg";
import Animated, { FadeIn, useReducedMotion } from "react-native-reanimated";
import { Press, T } from "@/src/components/ui";
import { Shine } from "@/src/analysis/Shine";
import { colors, space } from "@/src/theme";
import { DayInfo, scorePoints } from "@/src/series";
import { SoftEmpty, skyShine } from "./looks";
import { RankJourney } from "./RankJourney";

const H = 168, TOP = 26, BOTTOM = 26, LEFT = 34, RIGHT = 18;
const MODES = [["score", "Score", "Score trend dikhao"], ["rank", "Rank", "Rank journey dikhao"]] as const;

export function trendSummary(days: DayInfo[]) {
  const pts = scorePoints(days);
  if (!pts.length) return null;
  return { best: Math.max(...pts.map(p => p.score)), avg: Math.round(pts.reduce((a, p) => a + p.score, 0) / pts.length) };
}

/** Day-by-day live marks; missed days stay visible as dashed gaps. The switch on the card shows the All India Rank of the same days instead. */
export function ScoreTrend({ days }: { days: DayInfo[] }) {
  const router = useRouter();
  const reduced = useReducedMotion();
  const [w, setW] = useState(0);
  const [mode, setMode] = useState<"score" | "rank">("score");
  const pts = scorePoints(days);
  if (!pts.length) return <View testID="series-trend-empty">
    <Shine radius={22} {...skyShine}><SoftEmpty icon="chart-timeline-variant" title="Your score trend begins here." body="Finish a live day. When its result releases at 11:59 PM, your first point appears — no sample scores." /></Shine>
  </View>;

  const todayDay = days.find(d => d.isToday)?.day ?? 0;
  const maxDay = Math.max(pts[pts.length - 1].day, todayDay, pts[0].day + 1);
  const minDay = 1;
  const scores = pts.map(p => p.score);
  let lo = Math.floor((Math.min(...scores) - 20) / 50) * 50, hi = Math.ceil((Math.max(...scores) + 20) / 50) * 50;
  hi = Math.min(hi, Math.max(...pts.map(p => p.maximum)));
  if (hi - lo < 100) lo = hi - 100;
  const plotW = Math.max(1, w - LEFT - RIGHT), plotH = H - TOP - BOTTOM;
  const x = (d: number) => LEFT + ((d - minDay) / Math.max(1, maxDay - minDay)) * plotW;
  const y = (s: number) => TOP + (1 - (s - lo) / (hi - lo)) * plotH;
  const base = TOP + plotH;
  const best = pts.reduce((a, p) => (p.score > a.score ? p : a), pts[0]);
  const last = pts[pts.length - 1];
  const runs: typeof pts[] = [];
  pts.forEach((p, i) => { if (i && p.day - pts[i - 1].day === 1) runs[runs.length - 1].push(p); else runs.push([p]); });
  const gaps = pts.slice(1).map((p, i) => [pts[i], p]).filter(([a, b]) => b.day - a.day > 1);
  const missed = days.filter(d => d.tone === "missed" && d.day <= maxDay);
  const ticks = [0, 1, 2, 3].map(i => lo + ((hi - lo) * i) / 3);
  const xLabels = [...new Set([minDay, Math.round((minDay + maxDay) / 2), maxDay])];

  // A glossy sky-blue card; the marks line, its points and the newest mark are royal blue, the grid is white.
  return <View testID="series-trend"><Shine radius={22} {...skyShine} face={styles.card}>
    <View style={styles.head}>
      <T testID="series-trend-caption" size={10} color={colors.custom_tabInkSoft} style={styles.caption}>{mode === "rank" ? "All India Rank · upar = behtar" : `Marks out of ${pts[0].maximum}`}</T>
      <View testID="series-trend-mode" style={styles.modes}>
        {MODES.map(([key, label, says]) => <Press key={key} testID={"series-trend-mode-" + key} haptic={false} hitSlop={8} onPress={() => setMode(key)}
          accessibilityLabel={says} accessibilityState={{ selected: mode === key }} style={[styles.mode, mode === key && styles.modeOn]}>
          <T w="heavy" size={11.5} color={mode === key ? colors.custom_seriesRoyalInk : colors.custom_tabInk}>{label}</T>
        </Press>)}
      </View>
    </View>
    {mode === "rank" ? <RankJourney days={days} /> : <View style={{ height: H }} onLayout={e => setW(e.nativeEvent.layout.width)}>
      {w ? <Animated.View entering={reduced ? undefined : FadeIn.duration(500)} style={StyleSheet.absoluteFill}>
        <Svg width={w} height={H}>
          <Defs><LinearGradient id="trendArea" x1="0" y1="0" x2="0" y2="1"><Stop offset="0" stopColor={colors.custom_royalMid} stopOpacity={0.3} /><Stop offset="1" stopColor={colors.custom_royalMid} stopOpacity={0} /></LinearGradient></Defs>
          {ticks.map(t => <Line key={t} x1={LEFT} x2={w - RIGHT} y1={y(t)} y2={y(t)} stroke={t === lo ? colors.custom_tabInkSoft : colors.custom_tabChip} strokeOpacity={t === lo ? 0.45 : 1} strokeWidth={1} />)}
          {runs.filter(r => r.length > 1).map((r, i) => <Path key={"a" + i} fill="url(#trendArea)" d={`M${x(r[0].day)},${y(r[0].score)} ${r.slice(1).map(p => `L${x(p.day)},${y(p.score)}`).join(" ")} L${x(r[r.length - 1].day)},${base} L${x(r[0].day)},${base} Z`} />)}
          {gaps.map(([a, b]) => <Line key={"g" + a.day} x1={x(a.day)} y1={y(a.score)} x2={x(b.day)} y2={y(b.score)} stroke={colors.custom_tabInkSoft} strokeWidth={1.6} strokeDasharray="3 4" />)}
          {runs.filter(r => r.length > 1).map((r, i) => <Polyline key={"l" + i} points={r.map(p => `${x(p.day)},${y(p.score)}`).join(" ")} fill="none" stroke={colors.custom_royalMid} strokeWidth={2.2} strokeLinejoin="round" strokeLinecap="round" />)}
          {pts.map(p => p === best || p === last ? null : <Circle key={p.day} cx={x(p.day)} cy={y(p.score)} r={3} fill={colors.custom_royalMid} />)}
          {missed.map(d => <Circle key={"m" + d.day} cx={x(d.day)} cy={base} r={4} fill={colors.custom_missInk} />)}
          {todayDay && todayDay <= maxDay && !pts.some(p => p.day === todayDay) ? <Circle cx={x(todayDay)} cy={base} r={4} fill={colors.custom_todayInk} /> : null}
          <Circle cx={x(best.day)} cy={y(best.score)} r={5} fill={colors.custom_card} stroke={colors.custom_gold} strokeWidth={2} />
          {last !== best ? <Circle cx={x(last.day)} cy={y(last.score)} r={6} fill={colors.custom_royalMid} stroke={colors.surface} strokeWidth={2} /> : null}
          {last !== best ? <Rect x={Math.min(w - RIGHT - 38, x(last.day) - 19)} y={y(last.score) - 26} width={38} height={18} rx={9} fill={colors.custom_royalMid} /> : null}
        </Svg>
        {ticks.map(t => <T key={"t" + t} size={9.5} color={colors.custom_tabInkSoft} style={[styles.yLabel, { top: y(t) - 7 }]}>{Math.round(t)}</T>)}
        {xLabels.map(d => <T key={"x" + d} size={9.5} color={colors.custom_tabInkSoft} style={[styles.xLabel, { left: x(d) - 20 }]}>D{d}</T>)}
        <T w="heavy" size={9} color={colors.custom_goldDeep} style={[styles.tag, { left: x(best.day) - 30, top: y(best.score) - 22 }]}>BEST</T>
        {last !== best ? <T w="heavy" size={10.5} color={colors.custom_seriesRoyalInk} style={[styles.tag, { left: Math.min(w - RIGHT - 38, x(last.day) - 19) - 11, top: y(last.score) - 25 }]}>{last.score}</T> : null}
        {pts.map(p => <Press key={"p" + p.day} testID={"series-trend-point-" + p.day} haptic={false} onPress={() => router.push(`/result/${p.id}` as any)}
          accessibilityLabel={`Day ${p.day}: ${p.score} of ${p.maximum}. Open result`} style={[styles.hit, { left: x(p.day) - 22, top: y(p.score) - 22 }]}><View /></Press>)}
      </Animated.View> : null}
    </View>}
  </Shine></View>;
}

const styles = StyleSheet.create({
  // 11 inside the 2-point running edge: the card is the size it was with its 1-point line and 12 of padding.
  card: { paddingVertical: space.md - 1 },
  head: { flexDirection: "row", alignItems: "center", gap: space.sm, paddingHorizontal: space.lg - 2 },
  caption: { flex: 1, minWidth: 0 },
  // Score | Rank: two white chips, the open one royal blue. 30 high, 44 to the touch with their hit slop.
  modes: { flexDirection: "row", gap: 4, padding: 3, borderRadius: 18, backgroundColor: colors.custom_tabChip },
  mode: { minWidth: 56, height: 30, borderRadius: 15, alignItems: "center", justifyContent: "center", paddingHorizontal: 10 },
  modeOn: { backgroundColor: colors.custom_royalMid },
  yLabel: { position: "absolute", left: 4, width: 26, textAlign: "right" },
  xLabel: { position: "absolute", bottom: 4, width: 40, textAlign: "center" },
  tag: { position: "absolute", width: 60, textAlign: "center" },
  hit: { position: "absolute", width: 44, height: 44, borderRadius: 22 },
});
