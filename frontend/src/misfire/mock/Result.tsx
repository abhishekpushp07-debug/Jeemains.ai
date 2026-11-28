// A Misfire Mock's result: the score on the dark-red card, how many went to "Samajh gaya", each subject in its own
// colour, the chapters still weak, and every question with its key and its solution (from the paper it came from).
import React, { useState } from "react";
import { FlatList, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { imagePaths } from "@/src/assets/paperAssets";
import { piecesOf } from "@/src/assets/pieces";
import { PieceQuestion } from "@/src/components/Pieces";
import { AssetImage } from "@/src/components/AssetImage";
import { MathText } from "@/src/components/MathText";
import { GlossTabs } from "@/src/components/GlossTabs";
import { RedTabs } from "@/src/components/RedTabs";
import { Icon, IconName, Press, T } from "@/src/components/ui";
import { DCard, Pill, ScreenHeader } from "@/src/components/design";
import { ScoreRing } from "@/src/analysis/charts";
import { colors, radius, space, subjectColor } from "@/src/theme";
import { SHORT, SUBJECTS, Subject } from "@/src/choice/api";
import { ChoiceHero, ON_HERO, SUBJECT_LOOK, heroStyles } from "@/src/choice/looks";
import { useAuth } from "@/src/auth";
import { chapterLabel, chapterName } from "../parts";
import { useMockPictures } from "./pictures";
import { sendRight } from "./marking";
import { useMockPaths } from "./offline";
import { MARKS, Mock, Outcome } from "./store";

const OUT: Record<Outcome, { label: string; tone: string; icon: IconName }> = {
  correct: { label: "Sahi", tone: colors.success, icon: "check" },
  incorrect: { label: "Galat", tone: colors.error, icon: "close" },
  skipped: { label: "Chhoda", tone: colors.warning, icon: "minus" },
};
type Filter = "all" | Outcome;
const usedLabel = (s: number) => (s >= 60 ? `${Math.round(s / 60)} min` : `${s} sec`);
const key = (s: Subject) => s.toLowerCase();

export function MockResult({ mock, onBack }: { mock: Mock; onBack: () => void }) {
  const router = useRouter();
  const paths = useMockPaths(), signedIn = !!useAuth().user;
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const reading = Math.max(1, Math.min(width, 760) - 4 * space.lg - 2);
  const r = mock.result!;
  const sync = mock.sync || { todo: [], moved: [], refused: [], gone: [] };
  const subjects = SUBJECTS.filter((s) => mock.questions.some((q) => q.subject === s));
  const [subject, setSubject] = useState<Subject>(subjects[0] || "Physics");
  const [filter, setFilter] = useState<Filter>("all");
  const [qid, setQid] = useState("");
  const inSubject = mock.questions.filter((q) => q.subject === subject);
  const list = inSubject.filter((q) => filter === "all" || r.outcomes[q.id] === filter);
  const q = list.find((x) => x.id === qid) || list[0];
  useMockPictures(mock.questions, q?.id, true);
  const pct = r.maximum ? Math.max(0, Math.round((100 * r.score) / r.maximum)) : 0;
  const n = (o: Outcome) => inSubject.filter((x) => r.outcomes[x.id] === o).length;
  // The chapters with the most still wrong or left in this mock.
  const weak = Object.entries(mock.questions.reduce((m, x) => { if (r.outcomes[x.id] !== "correct") m[x.chapter] = (m[x.chapter] || 0) + 1; return m; }, {} as Record<string, number>))
    .sort((a, b) => b[1] - a[1]).slice(0, 4);
  const response = q ? mock.answers[q.id]?.value?.trim() || "" : "";
  const labelOf = (v: string) => q?.source_option_labels?.[v] || v;
  const outcome = q ? r.outcomes[q.id] : "skipped";
  const marks = outcome === "correct" ? MARKS.correct : outcome === "incorrect" ? MARKS.wrong : 0;

  return <View testID="mock-result-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
    <ScreenHeader testID="mock-result-header" title={mock.title} eyebrow="Offline Misfire · Result" backTestID="mock-result-back" onBack={onBack} />
    <ScrollView contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: insets.bottom + space.xxl, gap: space.md }} showsVerticalScrollIndicator={false}>
      <ChoiceHero testID="mock-result-hero">
        <T w="heavy" size={11} color={ON_HERO.soft} style={heroStyles.kicker}>{`OFFLINE MISFIRE #${mock.n} · RESULT`}</T>
        <View style={styles.ring}><ScoreRing percentage={pct} score={r.score} maximum={r.maximum} /></View>
        <T testID="mock-result-line" w="semibold" size={13} color={ON_HERO.soft} style={styles.center}>
          Accuracy {r.accuracy != null ? `${r.accuracy}%` : "—"} · {usedLabel(r.used)} lage · {mock.questions.length} sawaal
        </T>
        <View style={heroStyles.counts}>
          {(["correct", "incorrect", "skipped"] as Outcome[]).map((o, i) => <View key={o} style={[heroStyles.count, i > 0 && heroStyles.countLine]}>
            <T testID={`mock-result-${o}`} w="heavy" size={20} color={ON_HERO.ink}>{r[o]}</T>
            <T size={11} color={ON_HERO.soft}>{o === "skipped" ? "Chhode" : OUT[o].label}</T>
          </View>)}
        </View>
      </ChoiceHero>

      <DCard testID="mock-result-understood" style={{ gap: space.sm }}>
        {sync.moved.length ? <View style={styles.line}><Icon name="check-decagram" size={20} color={colors.success} />
          <T testID="mock-result-moved" w="heavy" size={14} color={colors.success} style={{ flex: 1 }}>{sync.moved.length} sawaal “Samajh gaya” mein chale gaye</T></View> : null}
        {sync.todo.length ? <View style={styles.line}><Icon name="cloud-upload-outline" size={20} color={colors.custom_softText} />
          <T testID="mock-result-waiting" w="bold" size={13.5} style={{ flex: 1 }}>{sync.todo.length} sahi sawaal “Samajh gaya” mein ja rahe hain. Internet aate hi pahunch jayenge.</T>
          {signedIn ? <Pill testID="mock-result-send" kind="outline" size="sm" label="Abhi bhejo" onPress={() => void sendRight(mock.id)} /> : null}</View> : null}
        {sync.refused.length ? <T testID="mock-result-refused" size={12.5} color={colors.muted}>{sync.refused.length} jawab website ki jaanch mein sahi nahi maane gaye, isliye galat gine gaye.</T> : null}
        {!r.correct ? <T testID="mock-result-none" size={13} color={colors.custom_softText}>Is baar koi sahi nahi hua. Neeche har sawaal ka solution dekho, phir naya mock do.</T> : null}
        {!paths.offline ? <Press testID="mock-result-misfire" onPress={() => router.push("/misfire" as any)} style={styles.link}>
          <T w="heavy" size={13} color={colors.brandText}>Misfire kholo</T><Icon name="arrow-right" size={15} color={colors.brandText} />
        </Press> : null}
      </DCard>

      <DCard testID="mock-result-subjects" style={{ gap: space.md }}>
        <T w="heavy" size={10.5} color={colors.brandText} style={styles.kicker}>SUBJECT-WISE</T>
        {r.subjects.map((s) => <View key={s.name} testID={`mock-result-subject-${key(s.name)}`} style={[styles.subject, { borderLeftColor: subjectColor(s.name) }]}>
          <View style={styles.subjectTop}>
            <T w="heavy" size={15} style={{ flex: 1 }}>{SHORT[s.name]}</T>
            <T w="mono" size={15}>{s.score}<T w="monoRegular" size={12} color={colors.muted}>/{s.maximum}</T></T>
          </View>
          <T size={12} color={colors.muted}>{s.correct} sahi · {s.incorrect} galat · {s.skipped} chhode · {s.count} sawaal</T>
          <View style={styles.track}><View style={[styles.fill, { width: `${(100 * s.correct) / Math.max(1, s.count)}%`, backgroundColor: subjectColor(s.name) }]} /></View>
        </View>)}
      </DCard>

      {weak.length ? <DCard testID="mock-result-weak" style={{ gap: space.sm }}>
        <T w="heavy" size={10.5} color={colors.brandText} style={styles.kicker}>INHE DOBARA DEKHO</T>
        {weak.map(([c, count]) => <View key={c} style={styles.line}>
          <View style={styles.weakDot} /><T w="bold" size={13.5} numberOfLines={2} style={{ flex: 1 }}>{chapterLabel(c)}</T><T w="heavy" size={13} color={colors.error}>{count}</T>
        </View>)}
      </DCard> : null}

      <View style={{ gap: 4, marginTop: space.sm }}>
        <T w="heavy" size={10.5} color={colors.brandText} style={styles.kicker}>SOLUTIONS</T>
        <T w="heavy" size={20} style={{ letterSpacing: -0.4 }}>Har sawaal ka sahi jawab</T>
      </View>
      {subjects.length > 1 ? <GlossTabs prefix="mock-result-subject" value={key(subject)} onChange={(k) => { const s = subjects.find((x) => key(x) === k); if (s) { setSubject(s); setQid(""); } }}
        items={subjects.map((s) => ({ key: key(s), label: SHORT[s], look: SUBJECT_LOOK[s], sub: String(mock.questions.filter((x) => x.subject === s).length) }))} /> : null}
      <RedTabs prefix="mock-result-filter" size={12} value={filter} onChange={(f) => { setFilter(f); setQid(""); }}
        items={[{ key: "all", label: `Sab ${inSubject.length}` }, { key: "incorrect", label: `Galat ${n("incorrect")}` }, { key: "skipped", label: `Chhode ${n("skipped")}` }, { key: "correct", label: `Sahi ${n("correct")}` }]} />
      {list.length ? <FlatList testID="mock-result-rail" horizontal showsHorizontalScrollIndicator={false} data={list} keyExtractor={(x) => x.id} contentContainerStyle={{ gap: 8, paddingRight: space.xl }}
        renderItem={({ item }) => {
          const o = OUT[r.outcomes[item.id] || "skipped"], sel = item.id === q?.id;
          return <Press testID={`mock-result-q-${item.number}`} onPress={() => setQid(item.id)} accessibilityLabel={`Question ${item.number}, ${o.label}${sel ? ", selected" : ""}`}
            style={[styles.qBox, { borderColor: sel ? colors.onSurface : o.tone }, sel && { backgroundColor: colors.onSurface }]}>
            <T w="mono" size={14} color={sel ? colors.custom_bar : colors.onSurface}>{item.number}</T>
            <Icon name={o.icon} size={11} color={sel ? colors.custom_bar : o.tone} />
          </Press>;
        }} /> : <DCard testID="mock-result-filter-empty"><T size={13} color={colors.muted}>Is filter mein {SHORT[subject]} ka koi sawaal nahi.</T></DCard>}

      {q ? <View testID="mock-solution-card" style={styles.card}>
        <View style={styles.cardHead}>
          <View style={{ flex: 1, minWidth: 0, gap: 1 }}>
            <T testID="mock-solution-title" w="heavy" size={16}>Question <T w="mono" size={16}>{q.number}</T></T>
            <T size={12} color={colors.muted} numberOfLines={1}>{SHORT[q.subject]} · {Object.keys(q.options || {}).length ? "Single correct" : "Numerical"}</T>
          </View>
          <View style={{ alignItems: "flex-end", gap: 3 }}>
            <View style={[styles.badge, { backgroundColor: OUT[outcome].tone }]}><T testID="mock-solution-outcome" w="heavy" size={11} color={colors.onSuccess}>{OUT[outcome].label.toUpperCase()}</T></View>
            <T w="mono" size={12} color={marks > 0 ? colors.success : marks < 0 ? colors.error : colors.muted}>{marks > 0 ? "+" : ""}{marks} marks</T>
          </View>
        </View>
        <T testID="mock-solution-source" size={12} color={colors.muted} numberOfLines={2}>{[q.source, q.source_number ? `Q${q.source_number}` : "", chapterName(q.chapter) && !q.source.includes(chapterName(q.chapter)) ? chapterName(q.chapter) : ""].filter(Boolean).join(" · ")}</T>
        {piecesOf(q) ? <PieceQuestion id={q.attempt_id} q={q} width={reading} testPrefix={`mock-review-${q.number}`} review={{ correct: q.accepted, response }} /> : <>
          {q.render_mode !== "source" && q.text ? <MathText testID="mock-solution-question-text" text={q.text} /> : null}
          {imagePaths(q.attempt_id, q, "question").map((path, i) => <AssetImage key={path} testID={`mock-solution-qimage-${i}`} path={path} label={`Question ${q.number}`} />)}
        </>}
        <View style={{ flexDirection: "row", gap: space.sm }}>
          <View style={[styles.answer, { backgroundColor: colors.custom_bar, borderColor: colors.custom_barLine }]}><T size={11} color={colors.muted}>Aapka jawab</T><T testID="mock-solution-yours" w="heavy" size={16}>{response ? labelOf(response) : "—"}</T></View>
          <View style={[styles.answer, { backgroundColor: colors.custom_successSoft, borderColor: colors.custom_successSoft }]}><T size={11} color={colors.success}>Answer key</T><T testID="mock-solution-key" w="heavy" size={16} color={colors.success}>{q.accepted.map(labelOf).join(" / ")}</T></View>
        </View>
        <T w="bold" size={11} color={colors.muted} style={{ letterSpacing: 1 }}>{q.solution_kind === "answer_key_only" ? "SUPPLIED ANSWER KEY" : "SOLUTION"}</T>
        {q.solution_kind === "answer_key_only" ? <T testID="mock-solution-key-only" size={13} color={colors.custom_softText}>Is sawaal ka sirf answer key mila hai. AI solution asli paper ke result mein dekh sakte ho.</T>
          : q.solution ? <MathText testID="mock-solution-text" size={14} text={q.solution} /> : null}
        {q.solution_kind !== "answer_key_only" ? imagePaths(q.attempt_id, q, "solution").map((path, i) => <AssetImage key={path} testID={`mock-solution-simage-${i}`} path={path} label={`Solution ${q.number}`} />) : null}
        {q.solution_kind !== "answer_key_only" && !q.solution && !q.solution_asset_count ? <T testID="mock-solution-none" size={13} color={colors.muted}>Likha hua solution nahi hai; upar answer key hai.</T> : null}
        <Press testID="mock-solution-paper" onPress={() => router.push(paths.paper(q.attempt_id))} style={styles.link}>
          <T w="heavy" size={13} color={colors.custom_softText}>Asli paper ka result</T><Icon name="arrow-right" size={15} color={colors.custom_softText} />
        </Press>
      </View> : null}

      <View style={{ gap: space.sm, marginTop: space.sm }}>
        <Pill testID="mock-result-new" kind="brand" size="lg" icon="fire" label="Naya mock banao" onPress={() => router.push(paths.make)} />
        <Pill testID="mock-result-all" kind="outline" label="Saare mocks" onPress={() => router.push(paths.list)} />
      </View>
    </ScrollView>
  </View>;
}

const styles = StyleSheet.create({
  ring: { alignItems: "center", paddingVertical: space.sm },
  center: { textAlign: "center" },
  kicker: { letterSpacing: 1.4 },
  line: { flexDirection: "row", alignItems: "center", gap: space.sm, flexWrap: "wrap" },
  link: { minHeight: 44, flexDirection: "row", alignItems: "center", gap: 6, alignSelf: "flex-start" },
  subject: { gap: 6, paddingLeft: space.md, borderLeftWidth: 4, borderRadius: 4 },
  subjectTop: { flexDirection: "row", alignItems: "center", gap: space.sm },
  track: { height: 6, borderRadius: radius.pill, backgroundColor: colors.custom_cardLine, overflow: "hidden" },
  fill: { height: 6, borderRadius: radius.pill },
  weakDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.custom_chipBlood },
  qBox: { width: 44, height: 48, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_card, borderWidth: 2 },
  card: { backgroundColor: colors.custom_card, borderRadius: 22, padding: space.lg, gap: space.md, borderWidth: 1, borderColor: colors.custom_cardLine },
  cardHead: { flexDirection: "row", alignItems: "flex-start", gap: space.sm },
  badge: { paddingHorizontal: 9, paddingVertical: 3, borderRadius: radius.pill },
  answer: { flex: 1, padding: space.md, borderRadius: 14, borderWidth: 1 },
});
