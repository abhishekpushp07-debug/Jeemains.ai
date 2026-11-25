// The Matched paper of a shift ("Attempt all matched"): OUR questions that matched its JEE Main questions, one at a time,
// with our options to tap and, under each, the JEE Main question it matched (without options). Submitting marks it on the
// phone (+4 / −1; nothing is sent anywhere) and opens the result: the marks, what was right and wrong, every solution.
// Open to everyone, signed in or not.
import React, { useEffect, useMemo, useRef, useState } from "react";
import { AppState, FlatList, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useCached } from "@/src/useCached";
import { Empty, ErrorBox, Press, Skeleton, T, buzz } from "@/src/components/ui";
import { DSheet, Pill, ScreenHeader } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { ScreenMotion } from "@/src/motion";
import { PillRow } from "@/src/misfire/parts";
import { colors, space } from "@/src/theme";
import { MatchedShift, getShift, shortDay, yearOf } from "@/src/matched/api";
import { ResultCard } from "@/src/matched/MatchedCard";
import { Answers, PaperQuestion as Q, Run, answered, clock, paperOf, runOf, saveLast, tally, verdict } from "@/src/matched/paper";
import { PaperQuestion, paperWidth } from "@/src/matched/PaperQuestion";

const YELLOW = colors.custom_glossYellow, INK = colors.custom_matchedInk, DOT = 44, GAP = 8;
const still = () => {};

/** The time taken so far. It counts only while the app is in front. */
function Clock({ run }: { run: Run }) {
  const [seconds, setSeconds] = useState(run.seconds);
  useEffect(() => {
    const tick = setInterval(() => { if (AppState.currentState === "active") setSeconds(run.seconds += 1); }, 1000);
    return () => clearInterval(tick);
  }, [run]);
  return <View testID="matched-paper-clock" accessibilityLabel={`Time ${clock(seconds)}`} style={styles.clock}>
    <Glyph name="clock-outline" size={15} color={colors.custom_softText} stroke={2} />
    <T w="mono" size={13} color={colors.custom_softText}>{clock(seconds)}</T>
  </View>;
}

/** The paper's questions as round numbers: yellow = answered, a dark ring = the one that is open. A tap opens it. */
function Numbers({ paper, answers, at, onGo }: { paper: Q[]; answers: Answers; at: number; onGo: (k: number) => void }) {
  const row = useRef<React.ElementRef<typeof ScrollView>>(null);
  useEffect(() => { row.current?.scrollTo({ x: Math.max(0, (at - 2) * (DOT + GAP)), animated: true }); }, [at]);
  return <ScrollView ref={row} testID="matched-paper-numbers" horizontal showsHorizontalScrollIndicator={false} style={styles.numbers} contentContainerStyle={styles.numbersRow}>
    {paper.map((q, k) => {
      const on = k === at, given = answered(q, answers[q.id]);
      return <Press key={q.id} testID={`matched-paper-number-${k}`} onPress={() => onGo(k)} scaleTo={0.94} accessibilityState={{ selected: on }}
        accessibilityLabel={`Question ${k + 1}${given ? ", jawab diya" : ", jawab nahi diya"}`} style={[styles.dot, given && styles.dotGiven, on && styles.dotOn]}>
        <T w="heavy" size={14} color={given ? INK : on ? colors.onSurface : colors.custom_softText}>{k + 1}</T>
      </Press>;
    })}
  </ScrollView>;
}

function Paper({ d, paper, run, onBack }: { d: MatchedShift; paper: Q[]; run: Run; onBack: () => void }) {
  const insets = useSafeAreaInsets();
  const width = paperWidth(useWindowDimensions().width, space.lg);
  const [answers, setAnswers] = useState<Answers>(run.answers);
  const [done, setDone] = useState(run.done);
  // A paper that was left half-way opens on its first question without an answer.
  const [at, setAt] = useState(() => Math.max(0, paper.findIndex(q => !answered(q, run.answers[q.id]))));
  const [asking, setAsking] = useState(false);
  const [show, setShow] = useState("");
  const page = useRef<React.ElementRef<typeof ScrollView>>(null);
  const year = yearOf(d.day), where = `Shift ${d.shift} · ${shortDay(d.day)}`;
  const q = paper[Math.min(at, paper.length - 1)];
  const given = paper.filter(x => answered(x, answers[x.id])).length, left = paper.length - given;

  const go = (to: number) => { if (paper[to]) { setAt(to); page.current?.scrollTo({ y: 0, animated: false }); } };
  const answer = (value: string) => { const next = { ...answers, [q.id]: value }; run.answers = next; setAnswers(next); };
  const submit = () => {
    run.done = true;
    void saveLast(d.id, tally(paper, answers), run.seconds);
    setAsking(false); setShow(""); setDone(true);
    buzz("success");
  };
  const again = () => { run.answers = {}; run.seconds = 0; run.done = false; setAnswers({}); setAt(0); setDone(false); };

  if (done) {
    const t = tally(paper, answers);
    const rows = paper.map((x, k) => ({ q: x, k, v: verdict(x, answers) })).filter(r => !show || r.v === show);
    return <>
      <ScreenHeader testID="matched-result-header" title="Aapka result" eyebrow="Matched paper" backTestID="matched-paper-back" onBack={onBack} />
      <FlatList testID="matched-result-list" data={rows} keyExtractor={r => r.q.id}
        renderItem={({ item }) => <PaperQuestion q={item.q} k={item.k} id={`matched-result-q-${item.k}`} year={year} value={answers[item.q.id] || ""} onChange={still} result={item.v} width={width} />}
        // A question with maths holds a typesetter: only the few near the screen are kept drawn.
        initialNumToRender={2} maxToRenderPerBatch={3} windowSize={5} showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: insets.bottom + space.xxl, gap: space.lg }}
        ListHeaderComponent={<View style={{ gap: space.md }}>
          <ResultCard line={`JEE Main ${year}`} marks={t.marks} max={t.max} right={t.right} wrong={t.wrong} left={t.left} time={clock(run.seconds)} onAgain={again} />
          <PillRow prefix="matched-result-show" value={show} onChange={setShow}
            items={[{ key: "", label: "All", count: paper.length }, { key: "right", label: "Sahi", count: t.right }, { key: "wrong", label: "Galat", count: t.wrong }, { key: "left", label: "Chhode", count: t.left }]} />
        </View>}
        ListEmptyComponent={<T testID="matched-result-none" size={13} color={colors.muted} style={styles.none}>Is tarah ka koi sawaal nahi hai.</T>} />
    </>;
  }

  const last = at === paper.length - 1;
  return <>
    <ScreenHeader testID="matched-paper-header" title="Matched paper" eyebrow={where} backTestID="matched-paper-back" onBack={onBack}
      right={<Press testID="matched-paper-submit-early" onPress={() => setAsking(true)} accessibilityLabel="Paper submit karo" style={styles.early}>
        <T w="heavy" size={13.5} color={colors.brandText}>Submit</T>
      </Press>} />
    <View style={styles.strip}>
      <Numbers paper={paper} answers={answers} at={at} onGo={go} />
      <Clock run={run} />
    </View>
    <ScrollView ref={page} testID="matched-paper-page" showsVerticalScrollIndicator={false} contentContainerStyle={styles.page}>
      <PaperQuestion key={q.id} q={q} k={at} id="matched-paper-q" year={year} value={answers[q.id] || ""} onChange={answer} width={width} />
    </ScrollView>
    <View testID="matched-paper-bar" style={[styles.bar, { paddingBottom: insets.bottom + 8 }]}>
      <Press testID="matched-paper-prev" disabled={at === 0} onPress={() => go(at - 1)} accessibilityLabel="Pichhla sawaal" style={styles.step}>
        <Glyph name="chevron-left" size={20} color={colors.onSurface} stroke={2} /><T w="heavy" size={14}>Pichhla</T>
      </Press>
      {last ? <Press testID="matched-paper-submit" onPress={() => setAsking(true)} accessibilityLabel="Paper submit karo" style={[styles.step, styles.submit]}>
        <T w="heavy" size={14} color={INK}>Submit paper</T><Glyph name="check" size={18} color={INK} stroke={2.4} />
      </Press> : <Press testID="matched-paper-next" onPress={() => go(at + 1)} accessibilityLabel="Agla sawaal" style={[styles.step, styles.next]}>
        <T w="heavy" size={14} color={colors.onSurfaceInverse}>Agla</T><Glyph name="chevron-right" size={20} color={colors.onSurfaceInverse} stroke={2} />
      </Press>}
    </View>
    <DSheet testID="matched-submit-sheet" visible={asking} onClose={() => setAsking(false)} title="Paper submit karein?" scroll={false}>
      <View style={styles.count}>
        <View style={styles.countBox}><T testID="matched-submit-given" w="heavy" size={24}>{given}</T><T size={12} color={colors.muted}>jawab diye</T></View>
        <View style={styles.countBox}><T testID="matched-submit-left" w="heavy" size={24} color={left ? colors.brandText : colors.onSurface}>{left}</T><T size={12} color={colors.muted}>chhode</T></View>
      </View>
      <T size={13.5} color={colors.custom_softText} style={styles.rule}>Sahi jawab +4, galat −1, chhoda hua 0. Submit ke baad jawab nahi badlenge; result aur solutions turant khulenge.</T>
      <Pill testID="matched-submit-yes" size="lg" label="Haan, submit karo" icon="check" bg={YELLOW} ink={INK} onPress={submit} />
      <Pill testID="matched-submit-no" kind="outline" label="Abhi nahi" onPress={() => setAsking(false)} />
    </DSheet>
  </>;
}

export default function MatchedPaperScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  // The same shift the list before this screen read: it is in memory already.
  const res = useCached<MatchedShift>(id ? `matched.shift.${id}` : null, getShift(id), false);
  const d = res.data;
  const paper = useMemo(() => (d ? paperOf(d) : []), [d]);
  const back = () => (router.canGoBack() ? router.back() : router.replace((id ? `/matched/${id}` : "/matched") as any));
  return <ScreenMotion>
    <View testID="matched-paper-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      {d && paper.length ? <Paper key={d.updated_at || 0} d={d} paper={paper} run={runOf(d.id, d.updated_at || 0)} onBack={back} /> : <>
        <ScreenHeader testID="matched-paper-header" title="Matched paper" eyebrow="JEE Main" backTestID="matched-paper-back" onBack={back} />
        <View style={styles.wait}>
          <ErrorBox testID="matched-paper-error" error={res.error} retry={res.reload} />
          {d ? <Empty testID="matched-paper-empty" icon="calendar-check-outline" title="Is shift ka paper abhi nahi bana" body="Jab hamare matched sawaalon ke jawab aa jayenge, paper yahan khulega." />
            : res.error ? null : <View testID="matched-paper-loading" style={{ gap: space.md }}><Skeleton h={56} /><Skeleton h={320} /></View>}
        </View>
      </>}
    </View>
  </ScreenMotion>;
}

const styles = StyleSheet.create({
  clock: { flexDirection: "row", alignItems: "center", gap: 5, height: 32, paddingHorizontal: 10, borderRadius: 16, backgroundColor: colors.custom_cardRaised },
  strip: { flexDirection: "row", alignItems: "center", gap: space.sm, paddingRight: space.lg, paddingBottom: space.md },
  numbers: { flex: 1 },
  numbersRow: { gap: GAP, paddingLeft: space.lg, paddingRight: space.sm },
  dot: { width: DOT, height: DOT, borderRadius: DOT / 2, alignItems: "center", justifyContent: "center", borderWidth: 1.5, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card },
  dotGiven: { backgroundColor: YELLOW, borderColor: YELLOW },
  dotOn: { borderColor: colors.onSurface, borderWidth: 2 },
  early: { minHeight: 44, minWidth: 44, paddingLeft: space.sm, alignItems: "flex-end", justifyContent: "center" },
  page: { paddingHorizontal: space.lg, paddingBottom: space.xl },
  bar: { flexDirection: "row", gap: space.md, paddingHorizontal: space.lg, paddingTop: 8, borderTopWidth: 1, borderTopColor: colors.custom_barLine, backgroundColor: colors.custom_bar },
  step: { flex: 1, height: 48, borderRadius: 24, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 4 },
  next: { backgroundColor: colors.onSurface, borderColor: colors.onSurface },
  submit: { backgroundColor: YELLOW, borderColor: YELLOW, gap: 6 },
  count: { flexDirection: "row", gap: space.md },
  countBox: { flex: 1, alignItems: "center", gap: 2, paddingVertical: space.md, borderRadius: 16, backgroundColor: colors.custom_cardRaised },
  rule: { lineHeight: 20 },
  none: { textAlign: "center", paddingVertical: space.xl },
  wait: { paddingHorizontal: space.lg, gap: space.md },
});
