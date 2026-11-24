import React, { useEffect, useRef, useState } from "react";
import { FlatList, StyleProp, StyleSheet, View, ViewStyle } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useRouter } from "expo-router";
import { Empty, Icon, Press, T } from "@/src/components/ui";
import { PastelSurface, Pill } from "@/src/components/design";
import { Shine } from "@/src/analysis/Shine";
import { chipEdges, colors, pastel, pastelEdges, SeriesTone, space } from "@/src/theme";
import { DAY_LOOK_ORDER, DAY_LOOKS, DayLook, dayLook } from "./dayLook";
import { AnalysisButton } from "./AnalysisButton";
import { istDate } from "@/src/navigation";
import { countdown, dayAction, dayAttempt, DayInfo, dayNote, istTime, Series, seriesDays } from "@/src/series";

const FACE = Object.fromEntries((Object.keys(pastel) as SeriesTone[]).map(t => [t, [pastel[t].from, pastel[t].to]])) as unknown as Record<SeriesTone, readonly [string, string]>;

/**
 * A big day card in its status colours (the two change places slowly), under a gloss and a glass glint that crosses from
 * corner to corner, inside a running edge of its own colour family.
 */
function ShineCard({ tone, testID, radius, face, children }: { tone: SeriesTone; testID: string; radius: number; face: StyleProp<ViewStyle>; children: React.ReactNode }) {
  return <View testID={testID}>
    <Shine radius={radius} ring={2} tones={FACE[tone]} edge={pastelEdges[tone]} gloss={colors.custom_seriesPastelGloss} glint={colors.custom_seriesPastelGlint} band={72} part={46} corner face={face}>{children}</Shine>
  </View>;
}

/**
 * TODAY: the live paper with its state-driven primary action. Once today's paper is submitted the blood-red button takes
 * over: before the result opens it says when it opens and shows the previous attempt's marks (`last`); after that it
 * shows today's marks and opens the analysis.
 */
export function TodayCard({ series, day, last }: { series: Series; day?: DayInfo; last?: DayInfo }) {
  const router = useRouter();
  const [, setTick] = useState(0);
  useEffect(() => { const t = setInterval(() => setTick(n => n + 1), 30000); return () => clearInterval(t); }, []);
  if (!day) {
    const before = series.today < series.first_date;
    const p = pastel[before ? "upcoming" : "done"];
    return <ShineCard testID="series-prelaunch" tone={before ? "upcoming" : "done"} radius={24} face={styles.today}>
      <T w="heavy" size={10} color={p.ink} style={styles.caps}>{before ? `STARTS ${istDate(series.first_date).toUpperCase()}` : "SERIES COMPLETE"}</T>
      <T w="heavy" size={20} color={colors.custom_pastelInk}>{before ? `The first challenge opens ${istDate(series.first_date)}.` : "The live series has ended."}</T>
      <T size={12.5} color={p.body}>{before ? `Your ${seriesDays(series)}-day schedule is below. Papers unlock only after publication and their opening time.` : "Continue in the practice archive. Live results stay separate."}</T>
    </ShineCard>;
  }
  const p = pastel[day.tone];
  const act = dayAction(day);
  const live = day.live;
  const attempted = !!live && !live.resumable;
  const openAnalysis = () => router.push({ pathname: "/result/[id]", params: { id: live!.id, from: "series-day" } });
  const marks = attempted ? live!.summary : null;
  const sealed = attempted && !marks && live!.status === "embargoed";
  const opensAt = istTime(day.slot.closes_at);
  const before = last ? dayAttempt(last)?.summary : null;
  const showClock = day.slot.state === "live" && !day.live && day.slot.last_start_at * 1000 > Date.now();
  return <ShineCard testID={"series-day-" + day.day} tone={day.tone} radius={24} face={styles.today}>
    <View style={styles.between}>
      <T w="heavy" size={10} color={p.ink} style={styles.caps}>DAY {day.day} · {day.label.toUpperCase()}</T>
      <T w="heavy" size={10} color={p.ink} style={styles.caps}>{istDate(day.date).toUpperCase()}</T>
    </View>
    <T testID="series-today-title" w="heavy" size={21} color={colors.custom_pastelInk}>{day.slot.title}</T>
    <T size={12.5} color={p.body}>75 Q · 180 min · +4 / −1</T>
    {showClock ? <View testID="series-last-start" style={styles.clock}>
      <Icon name="clock-outline" size={14} color={colors.custom_pastelInk} />
      <T w="bold" size={11} color={colors.custom_pastelInk}>Last start in {countdown(day.slot.last_start_at)}</T>
    </View> : null}
    {attempted ? <AnalysisButton big testID={"series-today-analysis-" + day.day} onPress={openAnalysis}
        label={marks ? `Aaj ke marks ${marks.score}/${marks.maximum}` : sealed ? `Aaj ka result ${opensAt}` : "Result taiyaar ho raha hai"}
        note={marks ? "Analysis dekho" : before ? `Pichhla attempt · Day ${last!.day}: ${before.score}/${before.maximum}` : sealed ? `Result ${opensAt} par khulega` : undefined} />
      : act ? <Pill testID={act.testID} label={act.label} iconRight={act.icon} bg={colors.custom_pastelInk} ink={p.cta} onPress={() => router.push(act.to as any)} />
      : <T testID="series-today-note" w="bold" size={12.5} color={p.body}>{dayNote(day)}</T>}
  </ShineCard>;
}

const CHIP = 52, GAP = 8;
// A chip's own colours, drawn once: blood red for a day still to come, parrot green for a day that is over, today's own colours for today.
const CHIP_FACE = Object.fromEntries(DAY_LOOK_ORDER.map(k => [k, <LinearGradient key={k} pointerEvents="none" colors={[DAY_LOOKS[k].from, DAY_LOOKS[k].to]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />])) as Record<DayLook, React.ReactElement>;
const SEEN = { itemVisiblePercentThreshold: 10 };
/** One chip per series day; opens on today. A tap runs the day's action (open analysis, resume or start); upcoming days just preview. */
export function DayStrip({ days, selected, onSelect }: { days: DayInfo[]; selected: number; onSelect: (d: DayInfo) => void }) {
  const list = useRef<FlatList<DayInfo>>(null);
  const index = Math.max(0, days.findIndex(d => d.day === selected));
  // Only the chips on screen shine; the rest stay still, so 50 days cost no more than the handful in view.
  const [seen, setSeen] = useState<[number, number]>(() => [Math.max(0, index - 2), Math.max(0, index - 2) + 8]);
  const onSeen = useRef(({ viewableItems }: { viewableItems: { index?: number | null }[] }) => {
    const at = viewableItems.map(v => v.index).filter((n): n is number => n != null);
    if (at.length) setSeen(old => { const lo = Math.min(...at), hi = Math.max(...at); return old[0] === lo && old[1] === hi ? old : [lo, hi]; });
  }).current;
  useEffect(() => {
    if (days.length) list.current?.scrollToIndex({ index: Math.max(0, index - 2), animated: true, viewPosition: 0 });
  }, [index, days.length]);
  return <FlatList ref={list} testID="series-day-strip" horizontal showsHorizontalScrollIndicator={false} data={days} keyExtractor={d => String(d.day)}
    getItemLayout={(_, i) => ({ length: CHIP + GAP, offset: (CHIP + GAP) * i, index: i })} initialScrollIndex={Math.max(0, index - 2)}
    onScrollToIndexFailed={() => {}} style={{ marginHorizontal: -space.lg, flexGrow: 0 }} contentContainerStyle={{ paddingHorizontal: space.lg }}
    initialNumToRender={12} windowSize={5} extraData={seen} onViewableItemsChanged={onSeen} viewabilityConfig={SEEN}
    renderItem={({ item: d, index: i }) => {
      const on = d.day === selected, kind = dayLook(d.tone), look = DAY_LOOKS[kind];
      const score = dayAttempt(d)?.summary;
      return <Press testID={"series-chip-" + d.day} onPress={() => onSelect(d)} accessibilityState={{ selected: on }}
        accessibilityLabel={`Day ${d.day}, ${istDate(d.date)}, ${d.label}${score ? `, ${score.score} of ${score.maximum}` : ""}`} style={styles.chipWrap}>
        <View style={styles.chipBox}>
          {/* Gloss, a corner-to-corner glint and a running edge; the glint reaches each chip a little after the one before it. */}
          <Shine radius={16} ring={on ? 3 : 2} backdrop={CHIP_FACE[kind]} edge={on ? chipEdges.chosen : look.edge} gloss={look.gloss} glint={look.glint}
            band={18} part={38} corner delay={(i % 8) * 140} rest={i < seen[0] || i > seen[1]} face={on ? styles.chipOn : styles.chip}>
            <T w="heavy" size={8.5} color={look.soft} style={{ letterSpacing: 1.2 }}>{d.isToday ? "TODAY" : "DAY"}</T>
            <T w="heavy" size={score ? 16 : 19} color={look.ink}>{d.day}</T>
            {score ? <T testID={"series-chip-score-" + d.day} w="heavy" size={9} color={look.ink} numberOfLines={1}>{score.score}/{score.maximum}</T> : null}
          </Shine>
        </View>
        <View style={[styles.chipDot, on && { backgroundColor: colors.onSurface }]} />
      </Press>;
    }} />;
}

/** Detail for the selected day: score, result, practice or opening time. */
export function DayCard({ day }: { day: DayInfo }) {
  const router = useRouter();
  const p = pastel[day.tone];
  const act = dayAction(day);
  const a = dayAttempt(day);
  const attempted = !!a && !a.resumable;
  const s = attempted ? a!.summary : null;
  const practice = attempted && a!.mode !== "series_live"; // a missed day's paper, done later from the archive
  return <ShineCard testID={"series-day-card-" + day.day} tone={day.tone} radius={22} face={styles.detail}>
    <View style={styles.between}>
      <T w="heavy" size={10} color={p.ink} style={styles.caps}>DAY {day.day} · {day.label.toUpperCase()}</T>
      <T w="heavy" size={10} color={p.ink} style={styles.caps}>{istDate(day.date).toUpperCase()}</T>
    </View>
    <T w="heavy" size={17} color={colors.custom_pastelInk} numberOfLines={2}>{day.slot.title}</T>
    <View style={[styles.between, { alignItems: "flex-end" }]}>
      <View style={{ flex: 1, alignItems: "flex-start", gap: space.sm }}>
        {attempted ? <AnalysisButton testID={"series-daycard-analysis-" + day.day}
            onPress={() => router.push({ pathname: "/result/[id]", params: { id: a!.id, from: "series-day" } })}
            label={s ? "Analysis dekho" : a!.status === "embargoed" ? `Result ${istTime(day.slot.closes_at)}` : "Result dekho"} /> : null}
        {/* A practised day can still be practised again; a live day's own action is the button above. */}
        {act && (!attempted || practice) ? <Pill testID={"series-daycard-action-" + day.day} size="sm" label={act.label} bg={colors.custom_pastelInk} ink={p.cta} onPress={() => router.push(act.to as any)} />
          : !attempted ? <T testID={"series-daycard-note-" + day.day} w="bold" size={12} color={p.body}>{dayNote(day)}</T> : null}
      </View>
      {s ? <View testID={"series-daycard-score-" + day.day} style={{ alignItems: "flex-end" }}>
        <T w="heavy" size={9} color={p.ink} style={{ letterSpacing: 1.4 }}>{practice ? "PRACTICE MARKS" : "MARKS"}</T>
        <T w="heavy" size={28} color={colors.custom_pastelInk}>{s.score}<T w="bold" size={12} color={p.body}>/{s.maximum}</T></T>
      </View> : null}
    </View>
  </ShineCard>;
}

/** Series attempts (live + archive practice), newest first. */
export function ResultsList({ items, dayOf, limit }: { items: any[]; dayOf: (date?: string) => number | undefined; limit: number }) {
  const router = useRouter();
  if (!items.length) return <View testID="series-history-empty" style={styles.empty}><Empty icon="chart-line-variant" title="Your first attempt starts your story." body="Series attempts and released results appear here. No sample scores are shown." /></View>;
  return <View style={{ gap: space.sm }}>
    {items.slice(0, limit).map(a => {
      const tone = a.summary ? "done" : a.resumable ? "today" : "upcoming";
      const p = pastel[tone];
      const day = dayOf(a.series_date);
      return <Press key={a.id} testID={"series-result-" + a.id} onPress={() => router.push(((a.resumable ? "/attempt/" : "/result/") + a.id) as any)} accessibilityLabel={`${a.title}. ${a.summary ? `${a.summary.score} of ${a.summary.maximum}` : a.resumable ? "In progress" : "Result pending"}`}>
        <PastelSurface tone={tone} style={styles.result}>
          <View style={{ flex: 1, gap: 2 }}>
            <T w="heavy" size={9.5} color={p.ink} style={{ letterSpacing: 1.4 }}>{day ? `DAY ${day} · ` : ""}{a.mode === "series_live" ? "LIVE" : "PRACTICE"}{a.series_date ? ` · ${istDate(a.series_date).toUpperCase()}` : ""}</T>
            <T w="heavy" size={14} color={colors.custom_pastelInk} numberOfLines={1}>{a.title}</T>
          </View>
          <T w="heavy" size={a.summary ? 15 : 12} color={colors.custom_pastelInk}>{a.summary ? `${a.summary.score}/${a.summary.maximum}` : a.resumable ? "Resume" : a.status === "embargoed" ? "11:59 PM" : "Preparing"}</T>
          <Icon name="chevron-right" size={20} color={colors.custom_pastelInk} />
        </PastelSurface>
      </Press>;
    })}
  </View>;
}

const styles = StyleSheet.create({
  caps: { letterSpacing: 1.8 },
  between: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: space.sm },
  // 18 inside the 2-point running edge: the big cards are the size they were with 20 of padding.
  today: { padding: 18, gap: space.sm },
  clock: { flexDirection: "row", alignItems: "center", gap: 6, alignSelf: "flex-start", backgroundColor: colors.custom_whiteA70, borderRadius: 999, paddingHorizontal: 12, height: 28, marginVertical: 2 },
  chipWrap: { width: CHIP, marginRight: GAP, alignItems: "center", gap: 6, paddingTop: 2 },
  chipBox: { width: CHIP },
  // A chip is 68 high as before: 64 inside its 2-point edge, or 62 inside the chosen day's 3-point edge.
  chip: { height: 64, alignItems: "center", justifyContent: "center", gap: 2 },
  chipOn: { height: 62, alignItems: "center", justifyContent: "center", gap: 2 },
  chipDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: "transparent" },
  detail: { padding: 18, gap: space.sm },
  result: { borderRadius: 18, paddingHorizontal: space.lg, paddingVertical: 12, minHeight: 60, flexDirection: "row", alignItems: "center", gap: space.sm },
  empty: { backgroundColor: colors.custom_card, borderRadius: 20, borderWidth: 1, borderColor: colors.custom_cardLine },
});
