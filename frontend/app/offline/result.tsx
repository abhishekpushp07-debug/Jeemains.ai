// A finished paper read from the copy this phone keeps (src/offline/papers.ts): the score, every question with the
// student's answer and the key, and the supplied solution. Nothing here asks the server for anything, so it opens
// without a line; what needs the server (full analysis, rank, AI solutions, reports, notes) is not on this screen.
import React, { useEffect, useMemo, useRef, useState } from "react";
import { FlatList, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { privateAssets, registerAssetManifest, setAssetAccount } from "@/src/api/client";
import { trustKept } from "@/src/assets/assetGrants";
import { imagePaths, subjectOf } from "@/src/assets/paperAssets";
import { piecesOf } from "@/src/assets/pieces";
import { AssetImage } from "@/src/components/AssetImage";
import { DCard as Card, ScreenHeader } from "@/src/components/design";
import { LearningStat } from "@/src/components/LearningTheme";
import { MathText } from "@/src/components/MathText";
import { PieceQuestion } from "@/src/components/Pieces";
import { SubjectTabs } from "@/src/components/player/SubjectNavigation";
import { Empty, Icon, IconName, Notice, Press, Skeleton, T } from "@/src/components/ui";
import { isResultLocked } from "@/src/mission/gate";
import { fmtSpent } from "@/src/navigation";
import { offlineIdentity } from "@/src/offline/door";
import { keptResult } from "@/src/offline/papers";
import { colors, radius, space } from "@/src/theme";

const OUT: Record<string, [string, IconName]> = { correct: [colors.success, "check"], incorrect: [colors.error, "close"], skipped: [colors.muted, "minus"], dropped: [colors.muted, "cancel"], bonus: [colors.custom_amber, "star"] };

export default function KeptResult() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { user, expired } = useAuth();
  const router = useRouter(), insets = useSafeAreaInsets(), { width } = useWindowDimensions();
  // undefined = being read; null = not on this phone (or this phone may not read it now); "locked" = not opened once yet.
  const [r, setR] = useState<any | null | undefined | "locked">(undefined);
  useEffect(() => {
    let alive = true;
    (async () => {
      const who = expired ? null : user ? { uid: user.id } : await offlineIdentity(); // a session the server ended opens nothing
      if (!who || !id) { if (alive) setR(null); return; }
      if (!user) setAssetAccount(who.uid); // the kept store of the account last confirmed on this phone; nothing is asked of the server
      const [kept, locked] = await Promise.all([keptResult(id), isResultLocked(id)]);
      if (!alive) return;
      if (kept && !locked) {
        // The pictures kept with this result are its pictures: they are drawn from the phone, never asked for again here.
        registerAssetManifest(id, kept.questions, true, "original", true);
        privateAssets.selectGroup(id);
        trustKept(id);
      }
      setR(kept ? (locked ? "locked" : kept) : null);
    })();
    return () => { alive = false; };
  }, [id, user, expired]);
  const back = () => (router.canGoBack() ? router.back() : router.replace("/offline/results" as any));
  const data = r && r !== "locked" ? r : null;

  return <View testID="kept-result-screen" style={[styles.screen, { paddingTop: insets.top + space.sm }]}>
    <ScreenHeader testID="kept-result-header" backTestID="kept-result-back" title={data?.title || "Result"} eyebrow={data?.exam ? `${data.exam} · Phone par rakha result` : "Phone par rakha result"} onBack={back} />
    <ScrollView contentContainerStyle={[styles.body, { paddingBottom: insets.bottom + space.xl }]}>
      {r === undefined ? <><Skeleton h={160} /><Skeleton h={120} /></> : null}
      {r === null ? <Card testID="kept-result-missing"><Empty icon="cloud-off-outline" title="Yeh result phone par nahi hai" body="Internet ke saath app kholo: aapke results apne aap phone par aa jaate hain." /></Card> : null}
      {r === "locked" ? <Card testID="kept-result-locked"><Empty icon="lock-outline" title="Pehle ek baar internet ke saath kholo" body="Is result ko pehli baar app mein internet ke saath kholna hai. Uske baad yeh bina internet bhi khulega." /></Card> : null}
      {data ? <Paper r={data} id={id!} width={width} /> : null}
    </ScrollView>
  </View>;
}

function Paper({ r, id, width }: { r: any; id: string; width: number }) {
  const s = r.summary, rows: any[] = r.questions;
  const subjects = useMemo(() => [...new Set(rows.map(subjectOf))], [rows]);
  const [subject, setSubject] = useState(subjects[0]);
  const list = useMemo(() => rows.filter((q) => subjectOf(q) === subject), [rows, subject]);
  const [qid, setQid] = useState("");
  const q = list.find((x) => x.id === qid) || list[0];
  const rail = useRef<FlatList>(null);
  const reading = Math.max(1, width - 4 * space.lg - 2);
  useEffect(() => {
    const i = list.findIndex((x) => x.id === q?.id);
    if (i >= 0) setTimeout(() => rail.current?.scrollToIndex({ index: i, viewPosition: 0.5, animated: false }), 50);
  }, [q?.id, list]);

  return <>
    <Notice testID="kept-result-note" tone="info">Yeh phone par rakhi copy hai. Poora analysis, rank aur AI solution internet ke saath app mein milte hain.</Notice>
    <LinearGradient testID="kept-result-score-card" colors={[colors.brandSecondary, colors.custom_series]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.score}>
      <T w="bold" size={11} color={colors.custom_whiteA70} style={styles.spaced}>YOUR SCORE</T>
      <T w="heavy" size={40} color={colors.onSurfaceInverse} testID="kept-result-score">{s.score}<T w="semibold" size={20} color={colors.custom_whiteA70}> / {s.maximum}</T></T>
      <T size={12} color={colors.custom_whiteA70}>{r.rules ? `+${r.rules.correct} / ${r.rules.wrong} / 0 marking` : ""}{s.total_seconds ? ` · ${fmtSpent(s.total_seconds)} used` : ""}</T>
    </LinearGradient>
    <View style={styles.row}>
      <LearningStat testID="kept-result-correct" label="Correct" value={s.correct} tone="completed" />
      <LearningStat testID="kept-result-incorrect" label="Incorrect" value={s.incorrect} tone="error" />
      <LearningStat testID="kept-result-skipped" label="Skipped" value={s.skipped} tone="active" />
    </View>
    <View testID="kept-result-navigator" style={styles.panel}>
      <SubjectTabs prefix="kept-subject" questions={rows} subject={subject} onSelect={(name) => { setSubject(name); setQid(""); }} wrap />
      <FlatList ref={rail} testID="kept-question-rail" horizontal showsHorizontalScrollIndicator={false} data={list} keyExtractor={(x) => x.id} contentContainerStyle={styles.rail}
        getItemLayout={(_, i) => ({ length: 52, offset: 52 * i, index: i })} onScrollToIndexFailed={() => {}}
        renderItem={({ item }) => {
          const [c, ic] = OUT[item.outcome] || OUT.skipped, on = item.id === q?.id;
          return <Press testID={"kept-question-" + item.number} onPress={() => setQid(item.id)} accessibilityLabel={`Question ${item.number}, ${item.outcome}${on ? ", selected" : ""}`}
            style={[styles.number, { backgroundColor: on ? colors.onSurface : colors.custom_card, borderColor: on ? colors.onSurface : c }]}>
            <T w="mono" size={14} color={on ? colors.custom_bar : colors.onSurface}>{item.number}</T>
            <Icon name={ic} size={11} color={on ? colors.custom_bar : c} />
          </Press>;
        }} />
    </View>
    {q ? <View testID="kept-solution-card" style={styles.card}>
      <View style={styles.head}>
        <View style={styles.grow}>
          <T w="heavy" size={16}>Question <T w="mono" size={16}>{q.number}</T></T>
          <T size={12} color={colors.muted} numberOfLines={1}>{subjectOf(q)} · {q.type === "integer" ? "Numerical" : "Single correct"}</T>
        </View>
        <View style={styles.right}>
          <View style={[styles.outcome, { backgroundColor: (OUT[q.outcome] || OUT.skipped)[0] }]}>
            <T w="heavy" size={11} color={q.outcome === "correct" ? colors.onSuccess : q.outcome === "incorrect" ? colors.onError : colors.surface}>{String(q.outcome || "").toUpperCase()}</T>
          </View>
          <T w="mono" size={12} color={q.marks > 0 ? colors.success : q.marks < 0 ? colors.error : colors.muted}>{q.marks > 0 ? "+" : ""}{q.marks} marks</T>
        </View>
      </View>
      {q.render_mode !== "source" && q.text ? <MathText testID="kept-question-text" text={q.text} /> : null}
      {piecesOf(q) ? <PieceQuestion id={id} q={q} width={reading} testPrefix={`kept-${q.number}`}
        review={{ correct: q.disposition === "bonus_all" || q.disposition === "dropped" ? [] : q.accepted_answers || [q.answer], response: q.response }} />
        : imagePaths(id, q, "question").map((path, i) => <AssetImage key={path} testID={`kept-qimage-${q.number}-${i}`} path={path} label={`Question ${q.number}`} />)}
      <View style={styles.row}>
        <View style={styles.yours}><T size={11} color={colors.muted}>Your answer</T><T w="heavy" size={16} testID="kept-your-answer">{q.response ? q.source_option_labels?.[q.response] || q.response : "—"}</T></View>
        <View style={styles.key}><T size={11} color={colors.success}>Answer key</T><T w="heavy" size={16} color={colors.success} testID="kept-answer-key">{(q.accepted_answers || [q.answer]).map((v: string) => q.source_option_labels?.[v] || v).join(" / ")}</T></View>
      </View>
      <T w="bold" size={11} color={colors.muted} style={styles.spaced}>{q.solution_kind === "answer_key_only" ? "SUPPLIED ANSWER KEY" : "SUPPLIED SOLUTION"}</T>
      {q.solution_kind !== "answer_key_only" && q.solution ? <MathText size={14} testID="kept-solution-text" text={q.solution} /> : null}
      {q.solution_kind === "answer_key_only" || (!q.solution && !q.solution_asset_count) ? <T testID="kept-no-solution" size={13} color={colors.muted}>Is sawaal ka likha hua solution nahi diya gaya. Answer key upar hai.</T> : null}
      {imagePaths(id, q, "solution").map((path, i) => <AssetImage key={path} testID={`kept-simage-${q.number}-${i}`} path={path} label={`Solution ${q.number}`} />)}
    </View> : null}
  </>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.surface }, body: { padding: space.lg, paddingTop: space.sm, gap: space.md },
  score: { gap: space.md, borderRadius: 24, padding: 20, borderWidth: 1, borderColor: colors.brandLine }, spaced: { letterSpacing: 1 },
  row: { flexDirection: "row", gap: space.sm }, grow: { flex: 1, minWidth: 0, gap: 1 }, right: { alignItems: "flex-end", gap: 3 },
  panel: { gap: space.md, padding: space.lg, borderRadius: 20, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card },
  rail: { gap: 8, paddingRight: space.xl },
  number: { width: 44, height: 48, borderRadius: 14, alignItems: "center", justifyContent: "center", borderWidth: 2 },
  card: { backgroundColor: colors.custom_card, borderRadius: 22, padding: space.lg, gap: space.md, borderWidth: 1, borderColor: colors.custom_cardLine },
  head: { flexDirection: "row", alignItems: "flex-start", gap: space.sm },
  outcome: { paddingHorizontal: 9, paddingVertical: 3, borderRadius: radius.pill },
  yours: { flex: 1, padding: space.md, borderRadius: 14, backgroundColor: colors.custom_bar, borderWidth: 1, borderColor: colors.custom_barLine },
  key: { flex: 1, padding: space.md, borderRadius: 14, backgroundColor: colors.custom_successSoft },
});
