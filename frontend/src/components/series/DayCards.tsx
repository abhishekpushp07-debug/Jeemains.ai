import React, { useEffect, useRef, useState } from "react";
import { FlatList, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { Empty, Icon, Press, T } from "@/src/components/ui";
import { PastelSurface, Pill } from "@/src/components/design";
import { colors, pastel, space } from "@/src/theme";
import { istDate } from "@/src/navigation";
import { countdown, dayAction, DayInfo, dayNote, Series, seriesDays } from "@/src/series";

/** TODAY: the live paper with its state-driven primary action. */
export function TodayCard({ series, day }: { series: Series; day?: DayInfo }) {
  const router = useRouter();
  const [, setTick] = useState(0);
  useEffect(() => { const t = setInterval(() => setTick(n => n + 1), 30000); return () => clearInterval(t); }, []);
  if (!day) {
    const before = series.today < series.first_date;
    const p = pastel[before ? "upcoming" : "done"];
    return <PastelSurface testID="series-prelaunch" tone={before ? "upcoming" : "done"} style={styles.today}>
      <T w="heavy" size={10} color={p.ink} style={styles.caps}>{before ? `STARTS ${istDate(series.first_date).toUpperCase()}` : "SERIES COMPLETE"}</T>
      <T w="heavy" size={20} color={colors.custom_pastelInk}>{before ? `The first challenge opens ${istDate(series.first_date)}.` : "The live series has ended."}</T>
      <T size={12.5} color={p.body}>{before ? `Your ${seriesDays(series)}-day schedule is below. Papers unlock only after publication and their opening time.` : "Continue in the practice archive. Live results stay separate."}</T>
    </PastelSurface>;
  }
  const p = pastel[day.tone];
  const act = dayAction(day);
  const showClock = day.slot.state === "live" && !day.live && day.slot.last_start_at * 1000 > Date.now();
  return <PastelSurface testID={"series-day-" + day.day} tone={day.tone} style={styles.today}>
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
    {act ? <Pill testID={act.testID} label={act.label} iconRight={act.icon} bg={colors.custom_pastelInk} ink={p.cta} onPress={() => router.push(act.to as any)} />
      : <T testID="series-today-note" w="bold" size={12.5} color={p.body}>{dayNote(day)}</T>}
  </PastelSurface>;
}

const CHIP = 52, GAP = 8;
/** One chip per series day; opens on today. */
export function DayStrip({ days, selected, onSelect }: { days: DayInfo[]; selected: number; onSelect: (day: number) => void }) {
  const list = useRef<FlatList<DayInfo>>(null);
  const index = Math.max(0, days.findIndex(d => d.day === selected));
  useEffect(() => {
    if (days.length) list.current?.scrollToIndex({ index: Math.max(0, index - 2), animated: true, viewPosition: 0 });
  }, [index, days.length]);
  return <FlatList ref={list} testID="series-day-strip" horizontal showsHorizontalScrollIndicator={false} data={days} keyExtractor={d => String(d.day)}
    getItemLayout={(_, i) => ({ length: CHIP + GAP, offset: (CHIP + GAP) * i, index: i })} initialScrollIndex={Math.max(0, index - 2)}
    onScrollToIndexFailed={() => {}} style={{ marginHorizontal: -space.lg, flexGrow: 0 }} contentContainerStyle={{ paddingHorizontal: space.lg }}
    initialNumToRender={12} windowSize={5}
    renderItem={({ item: d }) => {
      const on = d.day === selected, p = pastel[d.tone];
      return <Press testID={"series-chip-" + d.day} onPress={() => onSelect(d.day)} accessibilityState={{ selected: on }} accessibilityLabel={`Day ${d.day}, ${istDate(d.date)}, ${d.label}`} style={styles.chipWrap}>
        <PastelSurface tone={d.tone} style={[styles.chip, on && styles.chipOn]}>
          <T w="heavy" size={8.5} color={p.ink} style={{ letterSpacing: 1.2 }}>{d.isToday ? "TODAY" : "DAY"}</T>
          <T w="heavy" size={19} color={colors.custom_pastelInk}>{d.day}</T>
        </PastelSurface>
        <View style={[styles.chipDot, on && { backgroundColor: colors.onSurface }]} />
      </Press>;
    }} />;
}

/** Detail for the selected day: score, result, practice or opening time. */
export function DayCard({ day }: { day: DayInfo }) {
  const router = useRouter();
  const p = pastel[day.tone];
  const act = dayAction(day);
  const s = day.live?.summary;
  return <PastelSurface testID={"series-day-card-" + day.day} tone={day.tone} style={styles.detail}>
    <View style={styles.between}>
      <T w="heavy" size={10} color={p.ink} style={styles.caps}>DAY {day.day} · {day.label.toUpperCase()}</T>
      <T w="heavy" size={10} color={p.ink} style={styles.caps}>{istDate(day.date).toUpperCase()}</T>
    </View>
    <T w="heavy" size={17} color={colors.custom_pastelInk} numberOfLines={2}>{day.slot.title}</T>
    <View style={[styles.between, { alignItems: "flex-end" }]}>
      <View style={{ flex: 1, alignItems: "flex-start" }}>
        {act ? <Pill testID={"series-daycard-action-" + day.day} size="sm" label={act.label} bg={colors.custom_pastelInk} ink={p.cta} onPress={() => router.push(act.to as any)} />
          : <T testID={"series-daycard-note-" + day.day} w="bold" size={12} color={p.body}>{dayNote(day)}</T>}
      </View>
      {s ? <View testID={"series-daycard-score-" + day.day} style={{ alignItems: "flex-end" }}>
        <T w="heavy" size={9} color={p.ink} style={{ letterSpacing: 1.4 }}>MARKS</T>
        <T w="heavy" size={28} color={colors.custom_pastelInk}>{s.score}<T w="bold" size={12} color={p.body}>/{s.maximum}</T></T>
      </View> : null}
    </View>
  </PastelSurface>;
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
  today: { borderRadius: 24, padding: 20, gap: space.sm },
  clock: { flexDirection: "row", alignItems: "center", gap: 6, alignSelf: "flex-start", backgroundColor: colors.custom_whiteA70, borderRadius: 999, paddingHorizontal: 12, height: 28, marginVertical: 2 },
  chipWrap: { width: CHIP, marginRight: GAP, alignItems: "center", gap: 6, paddingTop: 2 },
  chip: { width: CHIP, height: 68, borderRadius: 16, alignItems: "center", justifyContent: "center", gap: 2, borderWidth: 2, borderColor: "transparent" },
  chipOn: { borderColor: colors.onSurface },
  chipDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: "transparent" },
  detail: { borderRadius: 22, padding: 20, gap: space.sm },
  result: { borderRadius: 18, paddingHorizontal: space.lg, paddingVertical: 12, minHeight: 60, flexDirection: "row", alignItems: "center", gap: space.sm },
  empty: { backgroundColor: colors.custom_card, borderRadius: 20, borderWidth: 1, borderColor: colors.custom_cardLine },
});
