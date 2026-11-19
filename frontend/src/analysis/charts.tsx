// Charts drawn in code with react-native-svg (already in the app): no chart library, no extra app size.
import React, { useState } from "react";
import { LayoutChangeEvent, StyleSheet, View } from "react-native";
import Svg, { Circle, G, Line, Path, Rect, Text as SvgText } from "react-native-svg";
import { Icon, Press, T } from "@/src/components/ui";
import { ProgressRing } from "@/src/components/design";
import { colors, fonts } from "@/src/theme";
import { An, Open, OUT_TONE, Q, RESULT, TONE, Tone, mmss } from "./format";
import { Key } from "./parts";

const AXIS = { fontFamily: fonts.medium, fontSize: 10, fill: colors.muted } as const;
const VALUE = { fontFamily: fonts.heavy, fontSize: 10.5, fill: colors.onSurface } as const;
const short = (v: number) => (Math.abs(v) >= 100 || Number.isInteger(v) ? String(Math.round(v)) : String(Math.round(v * 10) / 10));

function useWidth(): [number, (e: LayoutChangeEvent) => void] {
  const [w, setW] = useState(300);
  return [w, e => { const next = Math.round(e.nativeEvent.layout.width); if (next > 0 && next !== w) setW(next); }];
}
/** A round top value for the axis and how many steps it splits into (whole numbers for counts). */
function scale(max: number): [number, number] {
  if (!(max > 0)) return [1, 1];
  const p = 10 ** Math.floor(Math.log10(max)), f = max / p;
  if (f <= 1) return [p, p === 1 ? 1 : 2];
  if (f <= 2) return [2 * p, 2];
  if (f <= 4) return [4 * p, 4];
  if (f <= 5) return [5 * p, 5];
  if (f <= 8) return [8 * p, 4];
  return [10 * p, 5];
}
function Axis({ w, top, steps, y, left, unit = "" }: { w: number; top: number; steps: number; y: (v: number) => number; left: number; unit?: string }) {
  return <G>{Array.from({ length: steps + 1 }, (_, i) => (top * i) / steps).map(v => <G key={v}>
    <Line x1={left} x2={w} y1={y(v)} y2={y(v)} stroke={colors.custom_cardLine} strokeDasharray={v ? "3 3" : undefined} />
    <SvgText x={left - 5} y={y(v) + 3.5} textAnchor="end" {...AXIS}>{short(v)}{unit}</SvgText>
  </G>)}</G>;
}

export function ScoreRing({ percentage, size = 96 }: { percentage?: number | null; size?: number }) {
  const share = Math.max(0, Math.min(1, (percentage || 0) / 100));
  return <ProgressRing testID="a2-score-ring" size={size} stroke={9} value={share} track={colors.custom_whiteA15} color={colors.onSurfaceInverse} label={`Score ${percentage ?? 0}%`}>
    <T w="heavy" size={19} color={colors.onSurfaceInverse}>{percentage ?? 0}%</T>
  </ProgressRing>;
}

export type BarSeries = { name: string; tone: Tone };
/** Grouped bars (side by side) or stacked bars, with the value written on top. */
export function Bars({ data, series, stacked, height = 200, unit = "", testID }: { data: { label: string; values: (number | null | undefined)[] }[]; series: BarSeries[]; stacked?: boolean; height?: number; unit?: string; testID?: string }) {
  const [w, onLayout] = useWidth();
  const left = 30, topPad = 16, bottom = 22, plotH = height - topPad - bottom, plotW = w - left;
  const max = Math.max(0, ...data.map(d => (stacked ? d.values.reduce<number>((a, v) => a + (v || 0), 0) : Math.max(...d.values.map(v => v || 0)))));
  const [top, steps] = scale(max);
  const y = (v: number) => topPad + plotH - (plotH * v) / top;
  const group = plotW / Math.max(1, data.length), per = stacked ? 1 : series.length;
  const bar = Math.min(30, (group * 0.72) / per), gap = per > 1 ? Math.min(4, bar * 0.18) : 0;
  return <View testID={testID} onLayout={onLayout} style={{ gap: 8 }}>
    <Svg width={w} height={height}>
      <Axis w={w} top={top} steps={steps} y={y} left={left} unit={unit} />
      {data.map((d, gi) => {
        const cx = left + group * gi + group / 2;
        let run = 0;
        return <G key={d.label}>
          {d.values.map((raw, si) => {
            const v = raw || 0;
            if (stacked) {
              const y0 = y(run + v), h = y(run) - y0;
              run += v;
              return v > 0 ? <Rect key={si} x={cx - bar / 2} y={y0} width={bar} height={h} rx={3} fill={TONE[series[si].tone].fill} /> : null;
            }
            const x = cx - (per * bar + (per - 1) * gap) / 2 + si * (bar + gap);
            return <G key={si}>
              <Rect x={x} y={y(v)} width={bar} height={Math.max(v > 0 ? 2 : 0, y(0) - y(v))} rx={Math.min(4, bar / 3)} fill={TONE[series[si].tone].fill} />
              {v > 0 && bar >= 11 ? <SvgText x={x + bar / 2} y={y(v) - 4} textAnchor="middle" {...VALUE}>{short(v)}</SvgText> : null}
            </G>;
          })}
          {stacked && run > 0 ? <SvgText x={cx} y={y(run) - 4} textAnchor="middle" {...VALUE}>{short(run)}</SvgText> : null}
          <SvgText x={cx} y={height - 6} textAnchor="middle" {...AXIS} fill={colors.custom_softText}>{d.label}</SvgText>
        </G>;
      })}
    </Svg>
    {series.length > 1 ? <Key items={series.map(s => [s.name, s.tone])} /> : null}
  </View>;
}

export type LineSeries = { name: string; tone: Tone; values: (number | null | undefined)[]; dash?: boolean };
export function Lines({ series, xLabel, height = 210, testID }: { series: LineSeries[]; xLabel: (i: number) => string; height?: number; testID?: string }) {
  const [w, onLayout] = useWidth();
  const left = 30, topPad = 10, bottom = 22, right = 8, plotH = height - topPad - bottom, plotW = w - left - right;
  const n = Math.max(2, ...series.map(s => s.values.length));
  const [top, steps] = scale(Math.max(0, ...series.flatMap(s => s.values.map(v => v || 0))));
  const x = (i: number) => left + (plotW * i) / (n - 1), y = (v: number) => topPad + plotH - (plotH * v) / top;
  const marks = [0, 0.25, 0.5, 0.75, 1].map(f => Math.round((n - 1) * f));
  return <View testID={testID} onLayout={onLayout} style={{ gap: 8 }}>
    <Svg width={w} height={height}>
      <Axis w={w - right} top={top} steps={steps} y={y} left={left} />
      {[...new Set(marks)].map(i => <SvgText key={i} x={x(i)} y={height - 6} textAnchor={i === 0 ? "start" : i === n - 1 ? "end" : "middle"} {...AXIS}>{xLabel(i)}</SvgText>)}
      {series.map(s => <Path key={s.name} d={s.values.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)} ${y(v || 0).toFixed(1)}`).join(" ")} fill="none"
        stroke={TONE[s.tone].fill} strokeWidth={s.dash ? 2 : 2.6} strokeDasharray={s.dash ? "6 4" : undefined} strokeLinejoin="round" strokeLinecap="round" />)}
    </Svg>
    <Key items={series.map(s => [s.name, s.tone])} />
  </View>;
}

/** Score potential as steps: now, +careless, +risk, +time, maximum; the dashed line is the realistic target. */
export function Waterfall({ p }: { p: An["potential"] }) {
  const [w, onLayout] = useWidth();
  const step: Record<string, number> = Object.fromEntries(p.steps.map((s: any) => [s.key, s.marks]));
  let run = p.current;
  const rows: { name: string; base: number; v: number; label: string; tone: Tone }[] = [{ name: "Abhi", base: 0, v: p.current, label: short(p.current), tone: "mute" }];
  ([["careless", "Careless"], ["guard", "Risk"], ["reinvest", "Time"]] as const).forEach(([k, name]) => {
    rows.push({ name, base: Math.max(0, run), v: step[k] || 0, label: "+" + short(step[k] || 0), tone: "warn" });
    run += step[k] || 0;
  });
  rows.push({ name: "Max", base: 0, v: p.maximum, label: short(p.maximum), tone: "good" });
  const height = 230, left = 30, topPad = 22, bottom = 22, plotH = height - topPad - bottom, plotW = w - left;
  const [top, steps] = scale(Math.max(1, p.maximum, p.realistic, p.current));
  const y = (v: number) => topPad + plotH - (plotH * Math.max(0, v)) / top;
  const group = plotW / rows.length, bar = Math.min(40, group * 0.62);
  return <View testID="a2-potential-waterfall" onLayout={onLayout}>
    <Svg width={w} height={height}>
      <Axis w={w} top={top} steps={steps} y={y} left={left} />
      {rows.map((r, i) => {
        const cx = left + group * i + group / 2, y1 = y(r.base + Math.max(0, r.v)), h = Math.max(r.v > 0 ? 3 : 0, y(r.base) - y1);
        return <G key={r.name}>
          <Rect x={cx - bar / 2} y={y1} width={bar} height={h} rx={5} fill={TONE[r.tone].fill} />
          <SvgText x={cx} y={y1 - 5} textAnchor="middle" {...VALUE} fontSize={11.5}>{r.label}</SvgText>
          <SvgText x={cx} y={height - 6} textAnchor="middle" {...AXIS} fill={colors.custom_softText}>{r.name}</SvgText>
        </G>;
      })}
      <Line x1={left} x2={w} y1={y(p.realistic)} y2={y(p.realistic)} stroke={TONE.good.ink} strokeWidth={1.4} strokeDasharray="6 4" />
      <SvgText x={left + 4} y={y(p.realistic) - 5} fontFamily={fonts.heavy} fontSize={10.5} fill={TONE.good.ink}>Target {short(p.realistic)}</SvgText>
    </Svg>
  </View>;
}

const LANE: Record<string, number> = { correct: 2, incorrect: 1, skipped: 0 };
/** Every question as a dot: left = fast, right = slow, the dashed line is Par (ideal) time. Tap a dot to open its solution. */
export function SpeedMap({ an, onOpen }: { an: An; onOpen: Open }) {
  const [w, onLayout] = useWidth();
  const pts = an.questions.filter((q: Q) => q.time != null && q.par && q.outcome in LANE && (q.time > 0 || q.outcome !== "skipped")).map((q: Q) => ({
    id: q.id, n: q.number, o: q.outcome as string,
    x: Math.min(3, Math.round((100 * q.time) / q.par) / 100), y: LANE[q.outcome] + (((q.number * 37) % 100) / 100) * 0.56 - 0.28,
  }));
  if (!pts.length) return null;
  const height = 280, left = 50, topPad = 8, bottom = 24, right = 8, plotH = height - topPad - bottom, plotW = w - left - right;
  const x = (v: number) => left + (plotW * v) / 3, y = (v: number) => topPad + plotH - (plotH * (v + 0.5)) / 3;
  const zone = (x1: number, x2: number, lane: number, tone: Tone, label: string, end?: boolean) => <G key={label}>
    <Rect x={x(x1)} y={y(lane + 0.5)} width={x(x2) - x(x1)} height={y(lane - 0.5) - y(lane + 0.5)} fill={TONE[tone].fill} opacity={0.1} />
    <SvgText x={end ? x(x2) - 5 : x(x1) + 5} y={y(lane + 0.5) + 13} textAnchor={end ? "end" : "start"} fontFamily={fonts.bold} fontSize={10} fill={TONE[tone].ink}>{label}</SvgText>
  </G>;
  return <View testID="a2-speed-map" onLayout={onLayout}>
    <Svg width={w} height={height}>
      {zone(0, 1.25, 2, "good", "Perfect zone")}
      {zone(0, 0.5, 1, "bad", "Careless zone")}
      {zone(1.5, 3, 1, "warn", "Mehnga overtime", true)}
      {[0, 1, 2].map(l => <G key={l}>
        <Line x1={left} x2={w - right} y1={y(l - 0.5)} y2={y(l - 0.5)} stroke={colors.custom_cardLine} />
        <SvgText x={left - 6} y={y(l) + 3.5} textAnchor="end" {...AXIS} fill={colors.custom_softText}>{["Chhoda", "Galat", "Sahi"][l]}</SvgText>
      </G>)}
      {[0, 0.5, 1, 1.5, 2, 3].map(v => <SvgText key={v} x={x(v)} y={height - 7} textAnchor={v === 0 ? "start" : v === 3 ? "end" : "middle"} {...AXIS}
        fontFamily={v === 1 ? fonts.heavy : fonts.medium} fill={v === 1 ? colors.onSurface : colors.muted}>{v === 1 ? "Par" : v === 3 ? "3x+" : v + "x"}</SvgText>)}
      <Line x1={x(1)} x2={x(1)} y1={topPad} y2={topPad + plotH} stroke={colors.onSurface} strokeWidth={1.2} strokeDasharray="5 4" />
      {pts.map((p: any) => <Circle key={p.id} cx={x(p.x)} cy={y(p.y)} r={5.5} fill={TONE[OUT_TONE[p.o]].fill} stroke={colors.custom_card} strokeWidth={1.5} />)}
    </Svg>
    {/* Tap targets sit over the dots: a press on a drawn shape does not work in every place the app runs. */}
    {pts.map((p: any) => <Press key={p.id} testID={"a2-speed-dot-" + p.n} onPress={() => onOpen(p.id)} haptic={false} scaleTo={1} accessibilityLabel={`Q${p.n} ${RESULT[p.o]}. Solution kholo`}
      style={[styles.dotTap, { left: x(p.x) - 14, top: y(p.y) - 14 }]}>{null}</Press>)}
  </View>;
}

/** Where the class scored; the red column is the student's own range. */
export function Histogram({ dist }: { dist: An["overview"]["distribution"] }) {
  const most = Math.max(1, ...dist.bins.map((b: any) => b.count));
  return <View testID="a2-distribution" style={styles.hist} accessibilityLabel={`${dist.n} students ke Score ka chart`}>
    {dist.bins.map((b: any, i: number) => <View key={i} testID={b.you ? "a2-distribution-you" : undefined} style={styles.histCol}>
      <T size={10} w="bold" color={b.you ? colors.brandText : colors.muted}>{b.you ? "Aap" : b.count || ""}</T>
      <View style={[styles.histBar, { height: b.count ? Math.max(6, (96 * b.count) / most) : 2, backgroundColor: b.you ? colors.brandPrimary : colors.custom_dim }]} />
      <T size={9.5} color={colors.muted} numberOfLines={1}>{b.from}</T>
    </View>)}
  </View>;
}

/** One bar split into parts (marks earned / lost, time on right / wrong / unanswered). */
export function Split({ parts, testID, label }: { parts: [string, number | null | undefined, Tone][]; testID?: string; label: string }) {
  const total = Math.max(1, parts.reduce((a, [, v]) => a + Math.max(0, v || 0), 0));
  return <View testID={testID} accessibilityLabel={label} style={styles.split}>
    {parts.map(([k, v, tone]) => ((v || 0) > 0 ? <View key={k} style={{ width: `${(100 * (v || 0)) / total}%`, backgroundColor: TONE[tone].fill }} /> : null))}
  </View>;
}

/** Every question as a small numbered square, grouped by subject. */
export function QGrid({ an, onOpen }: { an: An; onOpen: Open }) {
  const groups: Record<string, Q[]> = {};
  an.questions.forEach((q: Q) => (groups[q.subject] = groups[q.subject] || []).push(q));
  return <View testID="a2-qgrid" style={{ gap: 14 }}>
    {Object.entries(groups).map(([name, qs]) => <View key={name} style={{ gap: 8 }}>
      <View style={styles.qgridHead}><T w="heavy" size={13.5}>{name}</T><T size={11.5} w="bold" color={colors.muted}>{qs.filter(q => q.outcome === "correct").length}/{qs.length} sahi</T></View>
      <View style={styles.qcells}>
        {qs.map(q => {
          const tone = OUT_TONE[q.outcome] || "mute", solid = tone !== "mute";
          return <Press key={q.id} testID={"a2-qgrid-q-" + q.number} onPress={() => onOpen(q.id)} haptic={false} scaleTo={0.92}
            accessibilityLabel={`Q${q.number} ${RESULT[q.outcome]}${q.time != null ? ", " + mmss(q.time) : ""}`}
            style={[styles.qcell, solid ? { backgroundColor: TONE[tone].fill, borderColor: TONE[tone].fill } : null]}>
            <T size={12.5} w="heavy" color={solid ? colors.custom_qInk : colors.muted}>{q.number}</T>
            {q.marked ? <Icon name="flag" size={9} color={solid ? colors.custom_qInk : TONE.warn.fill} style={styles.qflag} /> : null}
          </Press>;
        })}
      </View>
    </View>)}
  </View>;
}

const styles = StyleSheet.create({
  hist: { flexDirection: "row", alignItems: "flex-end", gap: 3, height: 132 },
  histCol: { flex: 1, alignItems: "center", justifyContent: "flex-end", gap: 3 },
  histBar: { width: "100%", borderTopLeftRadius: 4, borderTopRightRadius: 4 },
  split: { flexDirection: "row", height: 14, borderRadius: 7, overflow: "hidden", backgroundColor: colors.custom_qFresh },
  qgridHead: { flexDirection: "row", alignItems: "baseline", justifyContent: "space-between" },
  qcells: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  qcell: { width: 40, height: 40, borderRadius: 10, borderWidth: 1, borderColor: colors.custom_qFreshLine, backgroundColor: colors.custom_qFresh, alignItems: "center", justifyContent: "center" },
  qflag: { position: "absolute", top: 3, right: 3 },
  dotTap: { position: "absolute", width: 28, height: 28, borderRadius: 14 },
});
