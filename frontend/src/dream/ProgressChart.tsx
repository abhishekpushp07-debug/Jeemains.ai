// Dream Progress Chart: every full mock of one exam as a line (oldest → newest) climbing towards each dream college's
// target line (dashed, in that row's colour and number; solid once reached), so the student sees how far each dream
// still is. Tap any point to read that mock. Best, average of the last 3 and speed (marks per mock) sit above it.
// Pure SVG (react-native-svg is already in the app), so nothing is added to the app size.
import React, { useMemo, useState } from "react";
import { StyleSheet, View } from "react-native";
import Svg, { Circle, Defs, Line, LinearGradient as Grad, Path, Stop } from "react-native-svg";
import { Press, T } from "@/src/components/ui";
import { rankColors as colors, space } from "@/src/theme";
import { SERIF } from "@/src/rank/tones";
import { Dream, DreamExam, FULL, Mock } from "./store";

/** One colour per dream row (row 1 = first colour), shared by the chart's target lines and the rows' number rings. */
export const LINE_COLORS = [colors.custom_dreamLine1, colors.custom_dreamLine2, colors.custom_dreamLine3, colors.custom_dreamLine4, colors.custom_dreamLine5];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const day = (at: number) => { const d = new Date(at); return `${d.getDate()} ${MONTHS[d.getMonth()]}`; };
const WHITE = colors.onBrandPrimary, MUTED = colors.custom_rankSilverMuted;

/** The mocks the chart draws, oldest first: the newest `max`, or on a result screen those up to that mock. */
export function seriesOf(mocks: Mock[], mockId?: string, max = 30) {
  const at = mockId ? mocks.findIndex(m => m.id === mockId) : 0;
  return at < 0 ? [] : mocks.slice(at, at + max).reverse();
}

/** Marks gained per mock over the last (up to 5) mocks: the slope of a least-squares line. null with fewer than 2. */
export function speedOf(series: Mock[]) {
  const s = series.slice(-5);
  if (s.length < 2) return null;
  const mx = (s.length - 1) / 2, my = s.reduce((a, m) => a + m.score, 0) / s.length;
  let num = 0, den = 0;
  s.forEach((m, i) => { num += (i - mx) * (m.score - my); den += (i - mx) ** 2; });
  return num / den;
}

/** Y axis: round steps (10/20/25/50/100) with a little room above the highest target and below the lowest score. */
function scaleOf(values: number[]) {
  const min = Math.min(...values), max = Math.max(...values);
  const step = [10, 20, 25, 50, 100].find(s => Math.max(40, max - min) / s <= 5) ?? 100;
  let lo = Math.floor((min - step * 0.15) / step) * step;
  if (min >= 0 && lo < 0) lo = 0;
  return { lo, hi: Math.ceil((max + step * 0.15) / step) * step, step };
}

const L = 34, R = 46, TOP = 14, BOT = 22, GAP = 15;

export function ProgressChart({ exam, series, dreams, compact, here, testID }: {
  exam: DreamExam; series: Mock[]; dreams: Dream[]; compact?: boolean; here?: boolean; testID: string;
}) {
  const [w, setW] = useState(0);
  const [sel, setSel] = useState<number | null>(null);
  const n = series.length;
  const at = sel !== null && sel < n ? sel : n - 1;
  const H = compact ? 136 : 192, plotW = Math.max(1, w - L - R), plotH = H - TOP - BOT, base = TOP + plotH;
  const { lo, hi, step } = useMemo(() => scaleOf([...series.map(m => m.score), ...dreams.map(d => d.need)]), [series, dreams]);
  if (!n) return null;
  const x = (i: number) => L + (n === 1 ? plotW / 2 : (i * plotW) / (n - 1));
  const y = (v: number) => TOP + ((hi - v) / Math.max(1, hi - lo)) * plotH;
  const scores = series.map(m => m.score), last = scores[n - 1];
  const best = Math.max(...scores), avg = Math.round(scores.slice(-3).reduce((a, b) => a + b, 0) / Math.min(3, n));
  const speed = speedOf(series);
  const line = series.map((m, i) => `${i ? "L" : "M"}${x(i).toFixed(1)} ${y(m.score).toFixed(1)}`).join("");
  const ticks: number[] = [];
  for (let v = lo; v <= hi; v += step) ticks.push(v);
  // Target labels on the right, pushed apart so two close targets never overlap.
  const labels = dreams.map((d, i) => ({ d, i, at: y(d.need) })).sort((a, b) => a.at - b.at);
  labels.forEach((l, k) => { if (k) l.at = Math.max(l.at, labels[k - 1].at + GAP); });
  const shift = Math.max(0, (labels[labels.length - 1]?.at ?? 0) - base);
  labels.forEach(l => { l.at = Math.max(TOP - 6, l.at - shift); });
  const m = series[at], px = x(at);
  const half = n === 1 ? plotW / 2 : plotW / (2 * (n - 1));
  const sp = speed === null ? null : Math.round(speed * 10) / 10;
  return <View testID={testID} style={styles.wrap}
    accessibilityLabel={`${n} full mock. Last ${last}, best ${best}${sp !== null ? `, har mock mein ${sp} marks ki raftaar` : ""}.`}>
    <View style={styles.head}>
      <T w="bold" size={10} color={MUTED} style={styles.track} numberOfLines={1}>PROGRESS · {n} FULL MOCK{n > 1 ? "S" : ""}</T>
    </View>
    <View style={styles.stats}>
      <Stat label="BEST" value={String(best)} testID={`${testID}-best`} />
      <Stat label="AVG" value={String(avg)} sub={n >= 3 ? "last 3" : "sab mock"} testID={`${testID}-avg`} />
      <Stat label="RAFTAAR" testID={`${testID}-speed`} value={sp === null ? "—" : `${sp > 0 ? "+" : ""}${sp}`} sub={sp === null ? "2 mock do" : "per mock"}
        ink={sp === null ? MUTED : sp > 0 ? colors.custom_fLime : sp < 0 ? colors.custom_fPurpleDown : WHITE} />
    </View>
    {/* The chosen mock sits in its own bar above the chart, so it never covers a line or a target. */}
    <View testID={`${testID}-tip`} style={styles.tip}>
      <View style={styles.tipScore}>
        <T color={WHITE} style={styles.tipBig}>{m.score}</T>
        <T size={10.5} color={MUTED}> / {Math.max(FULL[exam], m.rawMax)}</T>
      </View>
      <View style={{ flex: 1, minWidth: 0 }}>
        <T size={11} color={colors.custom_rankSilver} numberOfLines={2}>{m.title}</T>
        <T size={10} color={MUTED} numberOfLines={1}>{day(m.at)}{at === n - 1 ? (here ? " · is mock" : " · last mock") : ` · mock ${at + 1} / ${n}`}</T>
      </View>
      {here && at === n - 1 ? <T w="bold" size={9.5} color={colors.custom_fPurpleHint} style={styles.here}>IS MOCK</T> : null}
    </View>
    <View style={{ height: H }} onLayout={e => setW(e.nativeEvent.layout.width)}>
      {w ? <>
        <Svg width={w} height={H}>
          <Defs>
            <Grad id={`${testID}-area`} x1="0" y1="0" x2="0" y2="1">
              <Stop offset="0" stopColor={colors.custom_fPurpleGlow} stopOpacity={0.45} />
              <Stop offset="1" stopColor={colors.custom_fPurpleGlow} stopOpacity={0} />
            </Grad>
          </Defs>
          {ticks.map(v => <Line key={v} x1={L} x2={L + plotW} y1={y(v)} y2={y(v)} stroke={colors.custom_dreamGrid} strokeWidth={1} />)}
          {dreams.map((d, i) => <Line key={d.id} x1={L} x2={L + plotW} y1={y(d.need)} y2={y(d.need)} stroke={LINE_COLORS[i % LINE_COLORS.length]}
            strokeWidth={1.6} strokeDasharray={last >= d.need ? undefined : "6 4"} strokeOpacity={0.95} />)}
          <Line x1={px} x2={px} y1={TOP} y2={base} stroke={colors.custom_fPurpleHint} strokeOpacity={0.35} strokeWidth={1} strokeDasharray="3 3" />
          {n > 1 ? <>
            <Path d={`${line}L${x(n - 1).toFixed(1)} ${base}L${x(0).toFixed(1)} ${base}Z`} fill={`url(#${testID}-area)`} />
            <Path d={line} stroke={colors.custom_fPurpleGlow} strokeOpacity={0.45} strokeWidth={7} fill="none" strokeLinejoin="round" strokeLinecap="round" />
            <Path d={line} stroke={WHITE} strokeWidth={2.4} fill="none" strokeLinejoin="round" strokeLinecap="round" />
          </> : null}
          {series.map((s, i) => <Circle key={s.id} cx={x(i)} cy={y(s.score)} r={i === at ? 6 : 3.4} fill={i === at ? colors.custom_fPurpleGlow : WHITE}
            stroke={WHITE} strokeWidth={i === at ? 2.4 : 0} />)}
        </Svg>
        {ticks.map(v => <T key={v} size={9.5} color={MUTED} style={[styles.tick, { top: y(v) - 7 }]}>{v}</T>)}
        {labels.map(l => <View key={l.d.id} testID={`${testID}-target-${l.i}`} style={[styles.target, { top: l.at - 8, left: L + plotW + 5 }]}>
          <View style={[styles.targetNum, { backgroundColor: LINE_COLORS[l.i % LINE_COLORS.length] }]}><T w="heavy" size={8.5} color={colors.custom_fOn}>{l.i + 1}</T></View>
          <T w="bold" size={9.5} color={LINE_COLORS[l.i % LINE_COLORS.length]}>{last >= l.d.need ? "✓" : l.d.need}</T>
        </View>)}
        {series.map((s, i) => <Press key={s.id} testID={`${testID}-point-${i}`} onPress={() => setSel(i)} haptic={false} scaleTo={1}
          accessibilityLabel={`${s.title}: ${s.score} marks, ${day(s.at)}`} accessibilityState={{ selected: i === at }}
          style={[styles.zone, { left: x(i) - half, width: half * 2, height: H }]}><View /></Press>)}
        <T size={9.5} color={MUTED} style={[styles.date, { left: L }]}>{day(series[0].at)}</T>
        {n > 1 ? <T size={9.5} color={MUTED} style={[styles.date, { right: R }]}>{day(series[n - 1].at)}</T> : null}
      </> : null}
    </View>
    {n === 1 ? <T testID={`${testID}-one`} size={11.5} color={MUTED}>Ek aur full mock do, tab progress ki line banegi.</T>
      : <T size={11} color={MUTED}>Kisi bhi point par tap karke us mock ka score dekho. Dotted line = dream ka target, number = neeche wala card.</T>}
  </View>;
}

function Stat({ label, value, sub, ink = WHITE, testID }: { label: string; value: string; sub?: string; ink?: string; testID: string }) {
  return <View style={styles.stat}>
    <T w="bold" size={9} color={MUTED} style={styles.track} numberOfLines={1}>{label}</T>
    <T testID={testID} color={ink} style={styles.statValue}>{value}</T>
    {sub ? <T size={9.5} color={MUTED} numberOfLines={1}>{sub}</T> : null}
  </View>;
}

const styles = StyleSheet.create({
  wrap: { gap: space.sm, padding: space.md, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_dreamBodyLine, backgroundColor: colors.custom_dreamGlass },
  head: { flexDirection: "row", alignItems: "center" },
  track: { letterSpacing: 1.6 },
  stats: { flexDirection: "row", gap: space.sm },
  stat: { flex: 1, minWidth: 0, gap: 1, paddingVertical: 6, paddingHorizontal: 8, borderRadius: 12, borderWidth: 1, borderColor: colors.custom_dreamBodyLine },
  statValue: { fontFamily: SERIF, fontSize: 20, lineHeight: 24 },
  tick: { position: "absolute", left: 0, width: L - 6, textAlign: "right" },
  target: { position: "absolute", flexDirection: "row", alignItems: "center", gap: 3 },
  targetNum: { width: 14, height: 14, borderRadius: 7, alignItems: "center", justifyContent: "center" },
  zone: { position: "absolute", top: 0 },
  tip: { flexDirection: "row", alignItems: "center", gap: space.md, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 12, borderWidth: 1,
    borderColor: colors.custom_fPurpleGlow, backgroundColor: colors.custom_dreamBody },
  tipScore: { flexDirection: "row", alignItems: "baseline" },
  tipBig: { fontFamily: SERIF, fontSize: 20, lineHeight: 24 },
  here: { letterSpacing: 1 },
  date: { position: "absolute", bottom: 2 },
});
