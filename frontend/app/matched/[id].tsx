// One JEE Main shift on Matched: its top card (how many questions matched, and "Attempt all matched": the shift's Matched
// paper), then every question that matched on its own card: the JEE question, ours under it, and the solution of both.
// Open to everyone, signed in or not.
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { FlatList, RefreshControl, View, useWindowDimensions } from "react-native";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useCached } from "@/src/useCached";
import { Empty, ErrorBox, Skeleton, T } from "@/src/components/ui";
import { ScreenHeader } from "@/src/components/design";
import { ScreenMotion } from "@/src/motion";
import { PillRow } from "@/src/misfire/parts";
import { colors, space } from "@/src/theme";
import { MatchedShift, SHORT, dayLabel, getShift, yearOf } from "@/src/matched/api";
import { AttemptCard } from "@/src/matched/MatchedCard";
import { Pair } from "@/src/matched/Pair";
import { Last, RIGHT, answered, paperOf, peekRun, readLast, tally } from "@/src/matched/paper";
import { PAD, kept } from "@/src/matched/parts";

export default function MatchedShiftScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  // A shift can be long: kept in memory while the app is open, not written to the phone.
  const res = useCached<MatchedShift>(id ? `matched.shift.${id}` : null, getShift(id), false);
  const d = res.data;
  const [subject, setSubject] = useState("");
  useEffect(() => () => kept.clear(), []);
  const subjects = d?.subjects || [];
  const on = subjects.some(s => s.name === subject) ? subject : "";
  const rows = useMemo(() => (d?.items || []).map((it, k) => ({ it, k })), [d]);
  const shown = useMemo(() => rows.filter(r => !on || r.it.subject === on), [rows, on]);
  // What is left of the screen's width inside a card, for the pictures.
  const width = Math.min(useWindowDimensions().width, 720) - 2 * space.lg - 2 * PAD - 2;
  const year = d ? yearOf(d.day) : "", where = d ? `${dayLabel(d.day)} · Shift ${d.shift}` : "";
  // The shift's Matched paper, and what the student has done with it: looked at again each time this screen is in front.
  const paper = useMemo(() => (d ? paperOf(d) : []), [d]);
  const [mine, setMine] = useState<{ given: number; done: boolean; marks: number; last: Last | null }>({ given: 0, done: false, marks: 0, last: null });
  useFocusEffect(useCallback(() => {
    if (!d) return;
    let live = true;
    const run = peekRun(d.id, d.updated_at || 0);
    setMine(m => ({ ...m, given: run ? paper.filter(q => answered(q, run.answers[q.id])).length : 0, done: !!run?.done, marks: run?.done ? tally(paper, run.answers).marks : 0 }));
    void readLast(d.id).then(last => { if (live) setMine(m => ({ ...m, last })); });
    return () => { live = false; };
  }, [d, paper]));
  const max = paper.length * RIGHT;
  const [cta, note] = mine.done ? ["Result dekho", `Aapka score: ${mine.marks} of ${max}`]
    : mine.given ? ["Continue paper", `${mine.given} of ${paper.length} ke jawab de chuke ho`]
      : mine.last ? ["Attempt again", `Pichhli baar: ${mine.last.marks} of ${mine.last.max} · ${mine.last.right} sahi`]
        : ["Attempt all matched", "Hamare woh sawaal jo JEE Main mein match hue.\nOptions ke saath, paper ki tarah solve karo."];
  return <ScreenMotion>
    <View testID="matched-shift-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <ScreenHeader testID="matched-shift-header" title={d ? `Shift ${d.shift} · ${dayLabel(d.day)}` : "Matched"} eyebrow={d ? `JEE Main ${year}` : "JEE Main"}
        backTestID="matched-shift-back" onBack={() => (router.canGoBack() ? router.back() : router.replace("/matched" as any))} />
      <FlatList testID="matched-shift-list" data={shown} keyExtractor={r => String(r.k)}
        renderItem={({ item }) => <Pair it={item.it} k={item.k} width={width} year={year} where={where} />}
        // A question with maths holds a typesetter: only the few near the screen are kept drawn.
        initialNumToRender={3} maxToRenderPerBatch={3} windowSize={5} showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: insets.bottom + space.xxl, gap: space.lg }}
        refreshControl={<RefreshControl testID="matched-shift-refresh" refreshing={res.refreshing} onRefresh={res.reload} />}
        ListHeaderComponent={<View style={{ gap: space.md }}>
          <ErrorBox testID="matched-shift-error" error={res.error} retry={res.reload} />
          {!d && !res.error ? <View testID="matched-shift-loading" style={{ gap: space.md }}><Skeleton h={96} /><Skeleton h={220} /></View> : null}
          {d ? <AttemptCard matched={d.matched} asked={d.asked} year={year} questions={paper.length} max={max} cta={cta} note={note}
            onAttempt={() => router.push(`/matched/paper/${d.id}` as any)} /> : null}
          {d?.items.length ? <T testID="matched-shift-list-title" w="bold" size={12} color={colors.custom_eyebrow} style={{ letterSpacing: 1.6, marginTop: space.xs }}>KAUN SA SAWAAL KISSE MATCH HUA</T> : null}
          {subjects.length > 1 ? <PillRow prefix="matched-subject" value={on} onChange={setSubject}
            items={[{ key: "", label: "All", count: d!.matched }, ...subjects.map(s => ({ key: s.name, label: SHORT[s.name] || s.name, count: s.n }))]} /> : null}
        </View>}
        ListEmptyComponent={d ? <Empty testID="matched-shift-empty" icon="calendar-check-outline" title="Is shift mein koi match nahi mila" body="Doosre shifts dekhne ke liye wapas jao." /> : undefined} />
    </View>
  </ScreenMotion>;
}
