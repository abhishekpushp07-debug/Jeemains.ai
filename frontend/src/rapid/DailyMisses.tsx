// The Misfires tab of the All India Rapid result: the cards of this round that were not answered right, each with the
// answer given, the right answer and the explanation. The server is asked only when the tab is first opened, and it
// sends only cards the student was shown: cards never reached stay sealed (all of India plays the same cards today).
import React, { useMemo, useState } from "react";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, View } from "react-native";
import { ErrorBox, T, tap } from "@/src/components/ui";
import { arena, rapidColors as colors, rapidSubjectColor as subjectColor } from "@/src/theme";
import { GameIcon } from "./Art";
import { GoldTitle } from "./arena";
import { Note } from "./parts";
import { RapidText } from "./RapidText";
import { SHORT } from "./scope";
import { DailyMiss, DailyResult, useDailyMisses } from "./daily";

const OUTCOME: Record<DailyMiss["outcome"], [string, string]> = {
  incorrect: ["Wrong", colors.error], timed_out: ["Timed out", colors.warning], skipped: ["Skipped", arena.muted],
};
const short = (s: string) => SHORT[s] || s;
const cards = (n: number) => `${n} card${n === 1 ? "" : "s"}`;

const MissCard = React.memo(function MissCard({ c }: { c: DailyMiss }) {
  const [label, ink] = OUTCOME[c.outcome], id = `rf-daily-miss-${c.i}`;
  return <View testID={id} style={styles.card}>
    <View style={styles.cardTop}>
      <T w="heavy" size={11} color={subjectColor(c.subject)} numberOfLines={1} style={styles.where}>CARD {c.i + 1} · {short(c.subject).toUpperCase()}</T>
      <View style={[styles.tag, { borderColor: ink }]}><T testID={`${id}-outcome`} w="heavy" size={10.5} color={ink}>{label}</T></View>
    </View>
    <T w="bold" size={11} color={arena.muted} numberOfLines={1}>{c.chapter}</T>
    <RapidText text={c.prompt} size={15} testID={`${id}-prompt`} />
    {c.formula ? <RapidText text={c.formula} size={17} testID={`${id}-formula`} /> : null}
    {c.outcome === "incorrect" && c.choice != null ? <RapidText testID={`${id}-chosen`} size={12} w="regular" color={colors.error} text={`You chose: ${c.options[c.choice]}`} /> : null}
    <RapidText testID={`${id}-correct`} size={12} w="bold" color={colors.success} text={`Correct: ${c.options[c.answer]}`} />
    {c.explain ? <RapidText testID={`${id}-explain`} size={11} w="regular" color={arena.muted} text={c.explain} /> : null}
  </View>;
});

export function DailyMisses({ result, uid }: { result: DailyResult; uid: string }) {
  const missed = result.total - result.correct;
  const q = useDailyMisses(uid, result.day, missed > 0);
  const [subject, setSubject] = useState("");
  const items = q.data?.items;
  const subjects = useMemo(() => {
    const by = new Map<string, number>();
    for (const c of items || []) by.set(c.subject, (by.get(c.subject) || 0) + 1);
    return [...by].map(([name, n]) => ({ name, n }));
  }, [items]);
  const on = subjects.some((s) => s.name === subject) ? subject : "";
  const shown = useMemo(() => (items || []).filter((c) => !on || c.subject === on), [items, on]);

  if (!missed) return <View testID="rf-daily-misses" style={styles.flawless}>
    <GameIcon name="target" size={72} />
    <GoldTitle size={22} center testID="rf-daily-misses-title">No misfires. Flawless!</GoldTitle>
    <Note>Every card right today.</Note>
  </View>;

  const of = (o: DailyMiss["outcome"]) => (items || []).filter((c) => c.outcome === o).length;
  const wrong = of("incorrect"), timed = of("timed_out"), skipped = of("skipped"), sealed = q.data?.sealed || 0;
  return <FlatList testID="rf-daily-misses" data={shown} keyExtractor={(c) => String(c.i)} renderItem={({ item }) => <MissCard c={item} />}
    // Each card may hold typeset maths, so only the few near the screen are kept drawn.
    initialNumToRender={4} maxToRenderPerBatch={4} windowSize={5} showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}
    ListHeaderComponent={<View style={styles.head}>
      <GoldTitle size={20} testID="rf-daily-misses-title">Misfires</GoldTitle>
      <T testID="rf-daily-misses-summary" w="bold" size={12} color={arena.aqua}>
        {!items ? (q.error ? "Could not get your cards" : "Getting your cards…")
          : items.length ? [wrong ? `${wrong} wrong` : "", timed ? `${timed} timed out` : "", skipped ? `${skipped} skipped` : ""].filter(Boolean).join(" · ") : "Nothing to show here"}
      </T>
      <ErrorBox testID="rf-daily-misses-error" error={q.error} retry={q.reload} />
      {!items && !q.error ? <ActivityIndicator testID="rf-daily-misses-loading" color={arena.aqua} /> : null}
      {subjects.length > 1 ? <View accessibilityRole="tablist" style={styles.tabs}>
        {[{ name: "", n: items!.length }, ...subjects].map((s) => {
          const picked = s.name === on, tint = s.name ? subjectColor(s.name) : arena.gold;
          return <Pressable key={s.name || "all"} testID={`rf-daily-misses-subject-${s.name ? s.name.toLowerCase() : "all"}`} accessibilityRole="tab" accessibilityState={{ selected: picked }}
            accessibilityLabel={`${s.name ? short(s.name) : "All subjects"}, ${cards(s.n)}`} onPress={() => { tap(); setSubject(s.name); }} style={[styles.tab, picked && { backgroundColor: tint }]}>
            <T w="heavy" size={12} color={picked ? arena.badgeInk : arena.muted}>{s.name ? short(s.name) : "All"}</T>
            <View style={[styles.count, { backgroundColor: picked ? arena.badgeInk : tint }]}><T w="heavy" size={10} color={picked ? arena.text : arena.badgeInk}>{s.n}</T></View>
          </Pressable>;
        })}
      </View> : null}
    </View>}
    ListFooterComponent={items ? <View style={styles.foot}>
      {sealed ? <Note testID="rf-daily-misses-sealed">{cards(sealed)} you did not reach {sealed === 1 ? "is" : "are"} not shown. All of India plays the same cards today, so their answers stay sealed.</Note> : null}
      {wrong + timed ? <Note testID="rf-daily-misses-weak">Wrong and timed-out cards are also kept in Weak cards in the lobby. Get one right there to clear it.</Note> : null}
    </View> : undefined} />;
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: 16, paddingTop: 4, paddingBottom: 32, gap: 10 },
  head: { gap: 6 }, foot: { gap: 2, paddingTop: 4 },
  flawless: { flex: 1, alignItems: "center", justifyContent: "center", gap: 8, padding: 24 },
  tabs: { flexDirection: "row", flexWrap: "wrap", gap: 6, paddingTop: 4 },
  tab: { height: 44, paddingHorizontal: 14, borderRadius: 22, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, backgroundColor: arena.panelHi },
  count: { minWidth: 20, height: 20, borderRadius: 10, paddingHorizontal: 5, alignItems: "center", justifyContent: "center" },
  card: { gap: 6, padding: 14, borderRadius: 18, backgroundColor: colors.custom_reading, borderWidth: 1.5, borderColor: arena.rim },
  cardTop: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 8 },
  where: { flexShrink: 1, letterSpacing: 1.2 },
  tag: { height: 22, paddingHorizontal: 8, borderRadius: 11, borderWidth: 1.5, alignItems: "center", justifyContent: "center" },
});
