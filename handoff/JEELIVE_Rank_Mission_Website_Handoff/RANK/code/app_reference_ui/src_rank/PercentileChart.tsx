// Percentile chart: 99.9 to 80 percentile, one line open at a time with its 20 most wanted seats.
import React, { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { ErrorBox, Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { rankColors as colors, space } from "@/src/theme";
import { Category, ChartLine, fmt, FormBody, predict, Seat } from "./api";
import { CATEGORY_LABEL } from "./tones";
import { Strip, Toggle } from "./controls";
import { SeatRow } from "./SeatList";

const CATS: Category[] = ["GEN", "EWS", "OBC-NCL", "SC", "ST"];

export function PercentileChart({ lines, branches, branchText, onBranch, onOpen }: {
  lines: ChartLine[]; branches: string[]; branchText: string; onBranch: () => void; onOpen: (s: Seat, body: FormBody) => void;
}) {
  const [category, setCategory] = useState<Category>("GEN");
  const [open, setOpen] = useState<number | null>(null);
  const [seats, setSeats] = useState<Seat[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tries, setTries] = useState(0);
  const body = (pct: number): FormBody => ({ percentile: pct, level: "normal", category, female: false, pwd: false, state: null, branches });
  const branchKey = branches.join("|");

  useEffect(() => {
    if (open === null) return;
    let live = true;
    setSeats(null); setError(null);
    predict({ percentile: open, level: "normal", category, female: false, pwd: false, state: null, branches: branchKey ? branchKey.split("|") : [], segment: "all", page: 1, page_size: 20 })
      .then(d => { if (live) setSeats(d.items); }).catch(e => { if (live) setError(e.message); });
    return () => { live = false; };
  }, [open, category, branchKey, tries]);

  return <Strip title="Percentile chart" testID="rank-chart">
    <View style={styles.wrap}>
      {CATS.map(c => <Toggle key={c} testID={`rank-chart-cat-${c}`} label={CATEGORY_LABEL[c]} on={category === c} onPress={() => setCategory(c)} />)}
      <Toggle testID="rank-chart-branch" label={branchText} caret on={branches.length > 0} onPress={onBranch} />
    </View>
    <View style={styles.head}>
      <T w="bold" size={11} color={colors.custom_eyebrow} style={styles.pct}>PERCENTILE</T>
      <T w="bold" size={11} color={colors.custom_eyebrow} style={styles.rank}>~ RANK</T>
      <T w="bold" size={11} color={colors.custom_eyebrow} style={styles.marks}>~ MARKS*</T>
    </View>
    {lines.map(l => {
      const on = open === l.pct;
      return <View key={l.pct}>
        <Press testID={`rank-chart-line-${l.pct}`} onPress={() => setOpen(on ? null : l.pct)} accessibilityState={{ expanded: on }} scaleTo={0.99} style={[styles.row, on && styles.rowOn]}>
          <T w="bold" size={14.5} style={styles.pct}>{l.pct.toFixed(1)}</T>
          <T size={14} style={styles.rank}>{fmt(l.rank)}</T>
          <T size={14} color={colors.custom_softText} style={styles.marks}>{l.marks}</T>
          <Glyph name={on ? "chevron-up" : "chevron-down"} size={16} color={colors.custom_dim} />
        </Press>
        {on ? <View testID={`rank-chart-seats-${l.pct}`} style={styles.seats}>
          {!seats && !error ? <ActivityIndicator color={colors.muted} style={{ paddingVertical: space.md }} /> : null}
          <ErrorBox error={error ?? undefined} retry={() => setTries(t => t + 1)} testID="rank-chart-error" />
          {seats && seats.length === 0 ? <T size={13} color={colors.muted}>Is percentile par 2026 mein koi seat nahi mili.</T> : null}
          {seats?.map((s, i) => <SeatRow key={s.prog} seat={s} testID={`rank-chart-seat-${i}`} onPress={() => onOpen(s, body(l.pct))} />)}
        </View> : null}
      </View>;
    })}
    <T size={11.5} color={colors.muted}>*Normal paper mein lagbhag marks. Seats: General list se shuru, bina home state, gender-neutral.</T>
  </Strip>;
}

const styles = StyleSheet.create({
  wrap: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  head: { flexDirection: "row", alignItems: "center", paddingRight: 20 },
  row: { flexDirection: "row", alignItems: "center", minHeight: 46, borderBottomWidth: 1, borderBottomColor: colors.custom_barLine },
  rowOn: { backgroundColor: colors.custom_cardRaised },
  pct: { flex: 1.1 },
  rank: { flex: 1.2 },
  marks: { flex: 0.9 },
  seats: { paddingLeft: space.sm, paddingBottom: space.sm, gap: space.md },
});
