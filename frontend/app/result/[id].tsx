import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { BackHandler, FlatList, Modal, ScrollView, StyleSheet, TextInput, View, useWindowDimensions } from "react-native";
import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { api, post, put, uuid } from "@/src/api/client";
import { loadResult } from "@/src/api/paperOpening";
import { useAuth } from "@/src/auth";
import { AssetImage } from "@/src/components/AssetImage";
import { ImageWarmup } from "@/src/components/player/ImageWarmup";
import { AiSolution } from "@/src/components/AiSolution";
import { MathText } from "@/src/components/MathText";
import { useCached } from "@/src/useCached";
import { LinearGradient } from "expo-linear-gradient";
import { Button, Chip, Empty, ErrorBox, Icon, IconName, Notice, Press, Sheet, Skeleton, T } from "@/src/components/ui";
import { DCard as Card, DSheet, Pill, ScreenHeader } from "@/src/components/design";
import { LearningStat, LearningTab } from "@/src/components/LearningTheme";
import { colors, fonts, LearningTone, learningTones, radius, space, subjectColor } from "@/src/theme";
import { fmtSpent, unixDate } from "@/src/navigation";
import { imagePaths, pieceWarmSizes, resultIsReleased, subjectOf, usePaperAssets } from "@/src/assets/paperAssets";
import { PIECE_ZOOM, piecesOf } from "@/src/assets/pieces";
import { usePieceZoom } from "@/src/assets/pieceZoom";
import { PieceQuestion } from "@/src/components/Pieces";
import { SubjectTabs, QuestionGrid } from "@/src/components/player/SubjectNavigation";
import { isResultLocked, unlockResult } from "@/src/mission/gate";
import { ShareGate } from "@/src/mission/ShareGate";
import { DreamMeter } from "@/src/dream/DreamMeter";
import { DreamCheerHost } from "@/src/dream/DreamCheer";
import { examOf, isFullMock, recordMock } from "@/src/dream/store";
import { useAnalysis } from "@/src/analysis/useAnalysis";
import { AnalysisBar, AnalysisBody, useAnalysisNav } from "@/src/analysis/Workspace";
import { SolutionInsight } from "@/src/analysis/SolutionInsight";
import { MisfireUnderstood } from "@/src/misfire/web/Understood";
import { An, index } from "@/src/analysis/format";
import { MatchedWith } from "@/src/matched/MatchedWith";
import { KeptOffer } from "@/src/offline/KeptOffer";
import { keepAiCopy } from "@/src/offline/papers";
import { track } from "@/src/jlTracker";

type Tab = "analysis" | "progress" | "confidence" | "rank" | "solutions";
const TABS: [Tab, string, IconName][] = [["analysis", "Analysis", "chart-donut"], ["progress", "Progress", "chart-line"], ["confidence", "Confidence", "gauge"], ["rank", "Rank", "podium"], ["solutions", "Solutions", "book-open-variant"]];
const TAB_TONE: Record<Tab, LearningTone> = { analysis: "maroon", progress: "active", confidence: "completed", rank: "saved", solutions: "error" };
const FILTERS: [string, string][] = [["all", "All"], ["incorrect", "Incorrect"], ["correct", "Correct"], ["skipped", "Skipped"], ["marked", "Marked"]];
// Analysis 2.0 tags (only when this attempt has a time record).
const TAG_FILTERS: [string, string][] = [["careless", "Careless"], ["overtime", "Overtime"], ["confused", "Confused"]];
const TAGGED: Record<string, string[]> = { careless: ["wasted"], overtime: ["slow_correct", "costly_overtime"], confused: ["confused"] };
const OUT: Record<string, [string, IconName]> = { correct: [colors.success, "check"], incorrect: [colors.error, "close"], skipped: [colors.muted, "minus"], dropped: [colors.muted, "cancel"], bonus: [colors.custom_amber, "star"] };
const LEGEND: [string, IconName, string][] = [["Correct", "check", colors.success], ["Incorrect", "close", colors.error], ["Skipped / other", "minus", colors.muted], ["Marked", "flag", colors.custom_neonAmber]];
const CATS = [["concept_gap", "Concept gap"], ["calculation", "Calculation"], ["silly_mistake", "Silly mistake"], ["time_pressure", "Time pressure"], ["misread", "Misread"], ["guess", "Guess"], ["other", "Other"]];
const matches = (q: any, f: string) => f === "all" || (f === "marked" ? q.marked : TAGGED[f] ? TAGGED[f].includes(q.tag) : q.outcome === f);
// What the student was looking at in this result; a different result starts on its Analysis.
const view = { id: "", tab: "analysis" as Tab, filter: "all", subject: "", qid: "", from: false };

function Pending({ r, id, reload }: { r: any; id: string; reload: () => void }) {
  const [job, setJob] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const failed = r.grading_status === "failed" || job?.status === "failed";
  useEffect(() => {
    if (!r.job_id) return;
    api("/jobs/" + r.job_id).then(setJob).catch(() => {});
  }, [r.job_id]);
  async function retry() {
    setBusy(true);
    setErr("");
    try { await post(`/jobs/${r.job_id}/retry`, {}); reload(); } catch (e: any) { setErr(e.message); }
    setBusy(false);
  }
  return (
    <Card testID="result-grading" style={{ gap: space.md }}>
      <Empty icon={failed ? "alert-circle-outline" : "progress-clock"} title={failed ? "Grading needs a retry" : "Submitted · preparing your result"} body={`Receipt ${String(r.receipt || id).slice(0, 8)}… is sealed. Your submitted answers can’t change.${failed ? " Retrying grading does not re-submit or alter them." : " This usually takes a few seconds."}`} />
      <ErrorBox error={err} />
      {failed && r.job_id ? <Button testID="result-retry-grading" label="Retry grading" busy={busy} onPress={retry} /> : <Button testID="result-check-again" kind="secondary" label="Check again" onPress={reload} />}
    </Card>
  );
}

// The short result (Score, counts, subjects): shown only when the full analysis could not be opened.
function Summary({ r }: { r: any }) {
  const s = r.summary;
  return (
    <View testID="result-summary" style={{ gap: space.md }}>
      <LinearGradient testID="result-score-card" colors={[colors.brandSecondary, colors.custom_series]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={learningStyles.score}>
        <T testID="result-score-version-label" w="bold" size={11} color={colors.custom_whiteA70} style={{ letterSpacing: 1 }}>YOUR SCORE · {r.score_version === "original" ? "ORIGINAL" : "REVISED"}</T>
        <T w="heavy" size={40} color={colors.onSurfaceInverse} testID="result-score">{s.score}<T w="semibold" size={20} color={colors.custom_whiteA70}> / {s.maximum}</T></T>
        <T testID="result-marking-and-time" size={12} color={colors.custom_whiteA70}>{r.rules ? `+${r.rules.correct} / ${r.rules.wrong} / 0 marking` : ""}{s.total_seconds ? ` · ${fmtSpent(s.total_seconds)} used` : ""}</T>
      </LinearGradient>
      <View style={{ flexDirection: "row", gap: space.sm }}>
        <LearningStat testID="result-correct" label="Correct" value={s.correct} tone="completed" />
        <LearningStat testID="result-incorrect" label="Incorrect" value={s.incorrect} tone="error" />
        <LearningStat testID="result-skipped" label="Skipped" value={s.skipped} tone="active" />
      </View>
      <View style={{ flexDirection: "row", gap: space.sm }}>
        <LearningStat testID="result-accuracy" label="Accuracy" value={s.accuracy != null ? s.accuracy + "%" : "—"} />
        <LearningStat testID="result-attempt-rate" label="Attempt rate" value={s.attempt_rate != null ? s.attempt_rate + "%" : "—"} />
        <LearningStat testID="result-penalty" label="Penalty" value={s.penalties ?? 0} />
      </View>
      {s.main_block ? <Notice tone="info">{`Main ${s.main_block.score}/${s.main_block.maximum} · Bonus ${s.bonus_block?.entered ? `${s.bonus_block.score}/${s.bonus_block.maximum}` : "not entered"}`}</Notice> : null}
      <Card style={{ gap: space.md }}>
        <T w="heavy" size={16}>Subject-wise</T>
        {Object.entries(s.subjects || {}).map(([name, g]: any) => (
          <View key={name} style={{ gap: 4 }} testID={"result-subject-" + name.toLowerCase()}>
            <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
              <T w="bold" size={14} color={subjectColor(name)}>{name}</T>
              <T w="bold" size={13}>{g.score} marks · {g.correct}/{g.count} correct</T>
            </View>
            <View style={{ height: 8, borderRadius: 4, backgroundColor: colors.custom_qFresh, overflow: "hidden" }}>
              <View style={{ width: `${g.count ? (g.correct / g.count) * 100 : 0}%`, height: "100%", backgroundColor: subjectColor(name) }} />
            </View>
          </View>
        ))}
      </Card>
      {Array.isArray(r.insights?.groups || r.insights) ? (
        <Card style={{ gap: space.sm }}>
          <T w="heavy" size={16}>Topics to revise</T>
          {(r.insights.groups || r.insights).filter((g: any) => g.incorrect + g.skipped > 0).slice(0, 6).map((g: any) => (
            <T key={g.label} size={13}>• {g.label}: {g.incorrect} incorrect, {g.skipped} skipped of {g.count}</T>
          ))}
        </Card>
      ) : null}
    </View>
  );
}

function Remote({ path, render }: { path: string; render: (d: any) => React.ReactNode }) {
  return <RemoteRequest key={path} path={path} render={render} />;
}
function RemoteRequest({ path, render }: { path: string; render: (d: any) => React.ReactNode }) {
  const [d, setD] = useState<any>(null);
  const [e, setE] = useState("");
  const [n, setN] = useState(0);
  useEffect(() => { const ctl = new AbortController(); api(path, { signal: ctl.signal }).then(d => { if (!ctl.signal.aborted) setD(d); }).catch(x => { if (!ctl.signal.aborted) setE(x.message); }); return () => ctl.abort(); }, [path, n]);
  if (e) return <ErrorBox error={e} retry={() => { setD(null); setE(""); setN(x => x + 1); }} />;
  if (!d) return <Skeleton h={140} />;
  return <>{render(d)}</>;
}

function Unavailable({ title, reason, testID }: { title: string; reason?: string; testID: string }) {
  return <Card testID={testID}><Empty icon="information-outline" title={title} body={reason} /></Card>;
}

function Solutions({ r, id, version, an, onAnalysis }: { r: any; id: string; version: string; an: An | null; onAnalysis?: () => void }) {
  const { width } = useWindowDimensions();
  // Each question carries its Analysis 2.0 tag, so Careless / Overtime / Confused can be filtered here too.
  const insight = useMemo<Record<string, any>>(() => (an ? index(an) : {}), [an]);
  const rows: any[] = useMemo(() => (r.questions || []).map((x: any) => ({ ...x, tag: insight[x.id]?.tag })), [r.questions, insight]);
  const filters = an?.quality?.available ? [...FILTERS, ...TAG_FILTERS] : FILTERS;
  const subjects = useMemo(() => [...new Set(rows.map(subjectOf))], [rows]);
  const [filter, setFilter] = useState(view.filter);
  const initial = rows.find((q) => q.id === view.qid);
  const [subject, setSubject] = useState(initial ? subjectOf(initial) : (subjects.includes(view.subject) ? view.subject : subjects[0]));
  const list = rows.filter((q) => subjectOf(q) === subject && matches(q, filter));
  const [qid, setQid] = useState(initial?.id || list[0]?.id || "");
  const q = rows.find((x) => x.id === qid && subjectOf(x) === subject && matches(x, filter)) || list[0];
  const [remembered, setRemembered] = useState<Record<string, string>>({});
  const [grid, setGrid] = useState(false);
  const warmPaths = usePaperAssets(id, rows, q?.id, true, version);
  const reading = Math.max(1, width - 4 * space.lg - 2);
  const pieceStep = usePieceZoom();
  const warmSizes = useMemo(() => pieceWarmSizes(id, rows, q?.id, reading, PIECE_ZOOM[pieceStep], version), [id, rows, q?.id, reading, pieceStep, version]);
  function chooseSubject(s: string) { if (q) setRemembered(old => ({ ...old, [subject]: q.id })); setSubject(s); setQid(remembered[s] || ""); }
  useEffect(() => { Object.assign(view, { filter, subject, qid: q?.id || "" }); }, [filter, subject, q?.id]);
  const rail = useRef<FlatList>(null);
  const [opened, setOpened] = useState<Record<string, "ok" | "err">>({});
  const [report, setReport] = useState(false);
  // AI step-by-step solutions generated on the JEELIVE backend (more arrive over time; refetched on open).
  const ai = useCached<any>(`ai.${id}`, (signal) => api(`/attempts/${id}/ai-solutions`, { signal }), false);
  const aiBy = useMemo(() => Object.fromEntries((ai.data?.items || []).map((x: any) => [x.question_id, x])), [ai.data]);
  // A paper the phone keeps gets the solutions just read, for reading without a line (src/offline/papers.ts).
  useEffect(() => { if (ai.data) void keepAiCopy(id, ai.data); }, [id, ai.data]);

  useEffect(() => {
    const i = list.findIndex((x) => x.id === q?.id);
    if (i >= 0) setTimeout(() => rail.current?.scrollToIndex({ index: i, viewPosition: 0.5, animated: false }), 50);
  }, [q?.id, subject, filter]); // eslint-disable-line react-hooks/exhaustive-deps
  const consult = useCallback(async (x: any) => {
    track("solution_viewed", { set_id: String(r.set_id || ""), question_no: Number(x.number) || 0 });
    try { await post(`/attempts/${id}/questions/${x.id}/solution-open`, {}); setOpened((o) => ({ ...o, [x.id]: "ok" })); } catch { setOpened((o) => ({ ...o, [x.id]: "err" })); }
  }, [id, r.set_id]);
  useEffect(() => { let live = true; Promise.resolve().then(() => { if (live && q && !opened[q.id]) void consult(q); }); return () => { live = false; }; }, [q, opened, consult]);

  return (
    <View style={{ gap: space.md }} testID="solution-navigator">
      <ImageWarmup paths={warmPaths} width={reading} sizes={warmSizes} />
      {onAnalysis ? <Press testID="solution-back-to-analysis" onPress={onAnalysis} accessibilityLabel="Analysis par wapas" style={learningStyles.backLink}>
        <Icon name="arrow-left" size={16} color={colors.brandText} /><T size={13} w="heavy" color={colors.brandText}>Analysis par wapas</T>
      </Press> : null}
      {/* As on jeelive.ai: pick the subject and the number first, then read the one question below. */}
      <View testID="solution-subject-question-panel" style={learningStyles.panelCard}>
        <View style={learningStyles.panelHead}>
          <T w="heavy" size={10.5} color={colors.brandText} style={learningStyles.kicker}>CHOOSE A SUBJECT</T>
          <T size={12} color={colors.muted}><T w="mono" size={12} color={colors.onSurface}>{rows.filter((x) => subjectOf(x) === subject).length}</T> questions</T>
        </View>
        <SubjectTabs prefix="solution-subject" questions={rows} subject={subject} onSelect={chooseSubject} wrap />
        <View style={learningStyles.solutionTools}>
          <View style={learningStyles.solutionPosition}>
            <T w="heavy" size={14}>{subject}</T>
            <T size={11.5} color={colors.muted}>Number chuno · aur ke liye side mein scroll karo</T>
          </View>
          <Press testID="solution-grid-open" onPress={() => setGrid(true)} style={learningStyles.gridButton}><Icon name="view-grid-outline" size={18} color={colors.brandText} /><T size={12} w="bold">Question grid</T></Press>
        </View>
        {list.length ? (
          <FlatList ref={rail} testID="solution-question-rail" horizontal showsHorizontalScrollIndicator={false} data={list} keyExtractor={(x) => x.id} contentContainerStyle={{ gap: 8, paddingRight: space.xl }}
            getItemLayout={(_, i) => ({ length: 52, offset: 52 * i, index: i })} onScrollToIndexFailed={() => {}}
            renderItem={({ item }) => {
              const [c, ic] = OUT[item.outcome] || OUT.skipped;
              const sel = item.id === q?.id;
              return (
                <Press testID={"solution-question-" + item.number} onPress={() => setQid(item.id)} accessibilityLabel={`Question ${item.number}, ${item.outcome}${item.marked ? ", marked" : ""}${sel ? ", selected" : ""}`}
                  style={{ width: 44, height: 48, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: sel ? colors.onSurface : colors.custom_card, borderWidth: 2, borderColor: sel ? colors.onSurface : c }}>
                  <T w="mono" size={14} color={sel ? colors.custom_bar : colors.onSurface}>{item.number}</T>
                  <Icon name={item.marked ? "flag" : ic} size={11} color={sel ? colors.custom_bar : c} />
                </Press>
              );
            }} />
        ) : (
          <Card testID="solution-empty-filter"><Empty icon="filter-off-outline" title={`No ${filter} questions in ${subject}.`} action={<Button testID="solution-show-all" kind="secondary" label="Show all questions" onPress={() => setFilter("all")} />} /></Card>
        )}
        <View testID="solution-legend" style={learningStyles.legend}>
          {LEGEND.map(([label, icon, tint]) => <View key={label} style={learningStyles.legendItem}><Icon name={icon} size={13} color={tint} /><T size={11.5} color={colors.custom_softText}>{label}</T></View>)}
        </View>
      </View>
      <View style={{ gap: 4 }}>
        <T w="heavy" size={10.5} color={colors.brandText} style={learningStyles.kicker}>UNDERSTAND THE WHY</T>
        <T testID="solution-title" w="heavy" size={20} style={{ letterSpacing: -0.4 }}>One question. A clearer understanding.</T>
        <T testID="solution-subject-position" size={12} color={colors.muted}>{subject} · Question {q?.number ?? "—"} · {q ? list.findIndex(item => item.id === q.id) + 1 : 0} of {list.length}</T>
      </View>
      <View style={learningStyles.filters}>
        {/* Counts follow the subject in view, the same list the number rail shows. */}
        {filters.map(([v, l]) => <Chip key={v} testID={"solution-filter-" + v} label={l} active={filter === v} count={rows.filter((x) => subjectOf(x) === subject && matches(x, v)).length} onPress={() => setFilter(v)} color={colors.onSurface} />)}
      </View>
      {q ? (
        <View testID="solution-card" style={{ backgroundColor: colors.custom_card, borderRadius: 22, padding: space.lg, gap: space.md, borderWidth: 1, borderColor: colors.custom_cardLine }}>
          <View style={learningStyles.cardHead}>
            <View style={{ flex: 1, minWidth: 0, gap: 1 }}>
              <T w="heavy" size={16}>Question <T w="mono" size={16}>{q.number}</T>{q.marked ? "  " : ""}{q.marked ? <Icon name="flag" size={15} color={colors.custom_neonAmber} /> : null}</T>
              <T size={12} color={colors.muted} numberOfLines={1}>{subjectOf(q)} · {q.type === "integer" ? "Numerical" : "Single correct"}</T>
            </View>
            <View style={{ alignItems: "flex-end", gap: 3 }}>
              <View style={{ paddingHorizontal: 9, paddingVertical: 3, borderRadius: radius.pill, backgroundColor: (OUT[q.outcome] || OUT.skipped)[0] }}>
                <T w="heavy" size={11} color={q.outcome === "correct" ? colors.onSuccess : q.outcome === "incorrect" ? colors.onError : colors.surface}>{q.outcome.toUpperCase()}</T>
              </View>
              <T w="mono" size={12} color={q.marks > 0 ? colors.success : q.marks < 0 ? colors.error : colors.muted}>{q.marks > 0 ? "+" : ""}{q.marks} marks</T>
            </View>
          </View>
          {an ? <SolutionInsight q={insight[q.id]} copy={an.copy} /> : null}
          {q.render_mode !== "source" && q.text ? <MathText testID="solution-question-text" text={q.text} /> : null}
          {/* Cut questions (website pieces): the key and the student's pick are marked on the options themselves. */}
          {piecesOf(q) ? <PieceQuestion id={id} q={q} width={reading} version={version} testPrefix={`review-${q.number}`}
            review={{ correct: q.disposition === "bonus_all" || q.disposition === "dropped" ? [] : q.accepted_answers || [q.answer], response: q.response }} />
            : imagePaths(id, q, "question", version).map((path, i) => <AssetImage key={path} testID={`solution-qimage-${q.number}-${i}`} path={path} label={`Question ${q.number}`} />)}
          {/* A Matched paper: the JEE Main question this one matched, with its own answer and solution. Nothing for any other paper. */}
          <MatchedWith paper={r.set_id} qid={q.id} width={reading} open />
          <View style={{ flexDirection: "row", gap: space.sm }}>
            <View style={{ flex: 1, padding: space.md, borderRadius: 14, backgroundColor: colors.custom_bar, borderWidth: 1, borderColor: colors.custom_barLine }}><T size={11} color={colors.muted}>Your answer</T><T w="heavy" size={16} testID="solution-your-answer">{q.response ? q.source_option_labels?.[q.response] || q.response : "—"}</T></View>
            <View style={{ flex: 1, padding: space.md, borderRadius: 14, backgroundColor: colors.custom_successSoft }}><T size={11} color={colors.success}>Answer key</T><T w="heavy" size={16} color={colors.success} testID="solution-answer-key">{(q.accepted_answers || [q.answer]).map((v: string) => q.source_option_labels?.[v] || v).join(" / ")}</T></View>
          </View>
          <T w="bold" size={11} color={colors.muted} style={{ letterSpacing: 1 }}>{q.solution_kind === "answer_key_only" ? "SUPPLIED ANSWER KEY" : "SUPPLIED SOLUTION"}</T>
          {q.solution_kind === "answer_key_only" ? (
            <T size={13} color={colors.custom_onReading} testID={"no-worked-solution-" + q.number}>{aiBy[q.id]?.state === "ready" ? "The source provides this key only. An AI generated step-by-step solution is shown below." : ai.error && !ai.data ? "The source provides this key only." : "The source provides this key only. No worked solution was supplied."}</T>
          ) : q.solution ? <MathText size={14} testID="solution-text" text={q.solution} /> : null}
          {q.solution_kind !== "answer_key_only" && !q.solution && !q.solution_asset_count ? <T testID="solution-not-supplied" size={13} color={colors.muted}>A worked solution is not available for this question yet. The supplied answer key is shown above.</T> : null}
          {imagePaths(id, q, "solution", version).map((path, i) => <AssetImage key={path} testID={`solution-simage-${q.number}-${i}`} path={path} label={`Solution ${q.number}`} />)}
          {ai.loading && !ai.data ? <Skeleton h={120} /> : ai.error && !ai.data ? (
            <Press testID="ai-solution-error" onPress={ai.reload} style={{ minHeight: 44, justifyContent: "center" }}><T size={12} w="bold" color={colors.brandText}>Couldn’t load AI solutions. Tap to retry</T></Press>
          ) : <AiSolution item={aiBy[q.id]} number={q.number} disclosure={ai.data?.disclosure} />}
          {opened[q.id] === "err" ? <Press testID="solution-consult-retry" onPress={() => consult(q)}><T size={12} w="bold" color={colors.brandText}>Couldn’t record that you viewed this solution. Retry</T></Press> : null}
          <Reflection key={`${q.id}.${version}`} id={id} q={q} version={version} state={r.review?.states?.[q.id] || r.review_states?.[q.id]} consulted={opened[q.id] === "ok"} />
          <Button testID="solution-report-button" kind="ghost" icon="flag-outline" label="Report a problem with this question" onPress={() => setReport(true)} color={colors.muted} />
        </View>
      ) : null}
      {report && q ? <ReportSheet visible onClose={() => setReport(false)} id={id} q={q} /> : null}
      <Modal visible={grid} transparent animationType="slide" onRequestClose={() => setGrid(false)}><View style={learningStyles.modal}><Sheet visible onClose={() => setGrid(false)} testID="solution-grid-sheet">
        <T testID="solution-grid-title" size={18} w="heavy">Solution question grid</T>
        <SubjectTabs prefix="solution-grid-subject" questions={rows} subject={subject} onSelect={chooseSubject} />
        <T testID="solution-grid-filter" size={12} color={colors.muted}>{subject} · {filter} · {list.length} questions</T>
        <QuestionGrid prefix="solution-grid-q" questions={list} onSelect={id => { setQid(id); setGrid(false); }} appearance={row => ({ bg: row.id === q?.id ? colors.onSurface : colors.custom_card, fg: row.id === q?.id ? colors.custom_bar : (OUT[row.outcome] || OUT.skipped)[0], icon: (OUT[row.outcome] || OUT.skipped)[1], label: row.outcome })} />
        <Button testID="solution-grid-close" kind="secondary" label="Close grid" onPress={() => setGrid(false)} />
      </Sheet></View></Modal>
    </View>
  );
}

function Reflection({ id, q, version, state, consulted }: { id: string; q: any; version: string; state?: any; consulted: boolean }) {
  const [s, setS] = useState<any>(state || { revision: 0, category: null, note: "", identified_error: false, wrote_note: false, reviewed_solution: false, retry_planned: false });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  async function save(patch: any) {
    const next = { ...s, ...patch };
    setBusy(true);
    setErr("");
    try {
      const res = await put(`/attempts/${id}/reviews/${q.id}`, { request_id: uuid(), revision: s.revision || 0, score_version: version, category: next.category, note: next.note || "", identified_error: next.identified_error, wrote_note: next.wrote_note, reviewed_solution: next.reviewed_solution, retry_planned: next.retry_planned });
      setS(res);
    } catch (e: any) { setErr(e.status === 409 ? "This reflection changed elsewhere. Reopen the result to load the latest." : e.message); }
    setBusy(false);
  }
  const steps: [string, string, boolean][] = [["identified_error", "Identified my error", !!s.category], ["wrote_note", "Wrote a note", !!(s.note || "").trim()], ["reviewed_solution", "Reviewed the solution", consulted], ["retry_planned", "Planned a retry", true]];
  return (
    <View testID="reflection-panel" style={{ gap: space.sm, padding: space.md, borderRadius: 16, backgroundColor: colors.custom_bar, borderWidth: 1, borderColor: colors.custom_barLine }}>
      <T w="heavy" size={14}>Your reflection {s.completed ? "· steps recorded" : ""}</T>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 6 }}>
        {CATS.map(([v, l]) => <Chip key={v} testID={"reflection-cat-" + v} label={l} active={s.category === v} onPress={() => setS({ ...s, category: s.category === v ? null : v })} />)}
      </ScrollView>
      <TextInput testID="reflection-note-input" value={s.note || ""} onChangeText={(t) => setS({ ...s, note: t.slice(0, 500) })} placeholder="Short private note (max 500)" placeholderTextColor={colors.muted} multiline
        style={{ minHeight: 60, borderRadius: 14, borderWidth: 1, borderColor: colors.custom_cardLine, padding: space.md, fontFamily: fonts.regular, fontSize: 14, color: colors.onSurface, backgroundColor: colors.custom_card, textAlignVertical: "top" }} />
      {steps.map(([k, l, ok]) => (
        <Press key={k} testID={"reflection-step-" + k} disabled={busy || (!ok && !s[k])} onPress={() => save({ [k]: !s[k] })} style={{ flexDirection: "row", alignItems: "center", gap: 8, minHeight: 40 }}>
          <Icon name={s[k] ? "checkbox-marked-circle" : "checkbox-blank-circle-outline"} size={22} color={s[k] ? colors.success : colors.muted} />
          <T size={13} w="medium">{l}</T>
        </Press>
      ))}
      <T size={10} color={colors.muted}>Completed means your review actions are recorded — not that mastery is proven.</T>
      <ErrorBox error={err} />
    </View>
  );
}

function ReportSheet({ visible, onClose, id, q }: { visible: boolean; onClose: () => void; id: string; q: any }) {
  const [cat, setCat] = useState("question");
  const [note, setNote] = useState("");
  const [receipt, setReceipt] = useState<any>(null);
  const [err, setErr] = useState("");
  async function send() {
    try { setReceipt(await post(`/attempts/${id}/questions/${q.id}/report-wrong`, { category: cat, context: "solutions", note: note.slice(0, 600) })); } catch (e: any) { setErr(e.message); }
  }
  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}><View style={learningStyles.modal}><Sheet visible onClose={onClose} testID="report-sheet">
      <T w="heavy" size={18}>Report Q{q?.number}</T>
      {receipt ? <Notice tone="success" testID="report-receipt">Report received ({receipt.status}). It will be reviewed — this does not instantly change the key or your score.</Notice> : (
        <>
          <View style={{ flexDirection: "row", gap: 6, flexWrap: "wrap" }}>
            {[["question", "Question"], ["key", "Answer key"], ["solution", "Solution"], ["display", "Display"]].map(([v, l]) => <Chip key={v} testID={"report-cat-" + v} label={l} active={cat === v} onPress={() => setCat(v)} />)}
          </View>
          <TextInput testID="report-note-input" value={note} onChangeText={setNote} placeholder="What looks wrong? (optional)" placeholderTextColor={colors.muted} multiline maxLength={600}
            style={{ minHeight: 70, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, padding: space.md, fontFamily: fonts.regular, fontSize: 14, color: colors.onSurface, textAlignVertical: "top" }} />
          <ErrorBox error={err} />
          <Button testID="report-submit" label="Send report" onPress={send} />
        </>
      )}
      <Button testID="report-close" kind="secondary" label="Close" onPress={onClose} />
    </Sheet></View></Modal>
  );
}

export default function Result() {
  const { user } = useAuth();
  const { id, from: fromParam } = useLocalSearchParams<{ id: string; from?: string }>();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [version, setVersion] = useState("original");
  const [received, setR] = useState<any>(null);
  const [receivedKey, setReceivedKey] = useState("");
  const r = receivedKey === `${user?.id}|${id}|${version}` ? received : null;
  const [status, setStatus] = useState(0);
  const [err, setErr] = useState("");
  const [tab, setTab] = useState<Tab>(() => {
    if (view.id !== id) Object.assign(view, { id, tab: "analysis", filter: "all", subject: "", qid: "", from: false });
    return view.tab;
  });
  const [from, setFrom] = useState(view.from); // Solutions was opened from a number or a chart in the analysis
  const [n, setN] = useState(0);
  const polls = useRef(0);
  // The page remembers where the analysis was scrolled, so coming back from a solution lands on the same chart.
  const page = useRef<React.ElementRef<typeof ScrollView>>(null);
  const kept = useRef(0), tracking = useRef(false);
  const show = useCallback((next: Tab, fromAnalysis = false) => {
    tracking.current = false;
    view.tab = next; view.from = fromAnalysis;
    setFrom(fromAnalysis);
    setTab(next);
  }, []);
  useEffect(() => {
    const t = setTimeout(() => {
      page.current?.scrollTo({ y: tab === "analysis" ? kept.current : 0, animated: false });
      tracking.current = tab === "analysis";
    }, 40);
    return () => clearTimeout(t);
  }, [tab]);
  const toTop = useCallback(() => { kept.current = 0; page.current?.scrollTo({ y: 0, animated: false }); }, []);
  const nav = useAnalysisNav(id!, toTop);
  const reload = useCallback(() => { polls.current = 0; setN((x) => x + 1); }, []);

  useEffect(() => {
    let alive = true;
    let t: any;
    if (!user) return;
    loadResult(id!, version).then((res) => {
      if (!alive) return;
      setErr(""); setReceivedKey(`${user.id}|${id}|${version}`);
      setR(res.data);
      setStatus(res.status);
      if (res.status === 202 && res.data?.grading_status !== "failed" && polls.current < 12) {
        polls.current += 1;
        t = setTimeout(() => setN((x) => x + 1), Math.max(res.retryAfterMs || res.data?.retry_after_ms || 2000, 1500 * polls.current) + Math.random() * 800);
      }
    }).catch((e) => alive && setErr(e.message));
    return () => { alive = false; clearTimeout(t); };
  }, [id, version, n, user]);

  const ready = resultIsReleased(status, r);
  // Analytics: the result once per opening, and the analysis each time its tab is shown.
  const setId = ready ? String(r?.set_id || "") : "";
  useEffect(() => { if (setId) track("result_viewed", { set_id: setId }); }, [setId]);
  useEffect(() => { if (setId && tab === "analysis") track("analysis_opened", { set_id: setId }); }, [setId, tab]);
  // Every released full mock is remembered with the account for the Dream College Meter (original score only).
  useEffect(() => {
    if (!ready || version !== "original" || !r?.summary) return;
    void recordMock({ id: id!, exam: r.exam, score: r.summary.score, maximum: r.summary.maximum, questions: r.count ?? r.questions?.length, title: r.title, kind: r.test_kind,
      at: typeof r.submitted_at === "number" ? r.submitted_at * 1000 : typeof r.submitted_at === "string" ? Date.parse(r.submitted_at) || undefined : undefined });
  }, [ready, r, id, version]);
  const releasedQuestions = useMemo(() => ready ? r.questions || [] : [], [ready, r]);
  usePaperAssets(id!, releasedQuestions, undefined, true, version, !!ready && tab !== "solutions");
  const analysis = useAnalysis(id!, user?.id, version, !!ready, nav.compare, nav.vs);
  // A number, a bar or a chip in the analysis opens that question's solution.
  const openQuestion = useCallback((qid: string) => {
    const q = releasedQuestions.find((x: any) => x.id === qid);
    if (!q) return;
    const tagged = { ...q, tag: analysis.data ? index(analysis.data)[qid]?.tag : undefined };
    Object.assign(view, { qid, subject: subjectOf(q), filter: matches(tagged, view.filter) ? view.filter : "all" });
    show("solutions", true);
  }, [releasedQuestions, analysis.data, show]);
  // "Galtiyan dobara": a separate untimed attempt with only the wrong and skipped questions. The original result stays.
  const [retry, setRetry] = useState<"" | "ask" | "busy">("");
  const [retryErr, setRetryErr] = useState("");
  async function startRetry() {
    setRetry("busy"); setRetryErr("");
    try {
      const next = await post(`/attempts/${id}/retry`, { start_key: uuid(), score_version: version });
      setRetry("");
      router.push(`/attempt/${next.id}`);
    } catch (e: any) { setRetryErr(e.message); setRetry("ask"); }
  }
  // A fresh submission shows the Mission card first ("Share to view results"); the result keeps loading behind it.
  const [gate, setGate] = useState<"checking" | "locked" | "open">("checking");
  useEffect(() => { let live = true; isResultLocked(id!).then(l => { if (live) setGate(l ? "locked" : "open"); }); return () => { live = false; }; }, [id]);
  // Opened straight from an All India day: back goes up to the AITS Analysis list (then that list's back reaches the series page).
  const leave = () => (fromParam === "series-day" ? router.replace("/series-analysis") : router.canGoBack() ? router.back() : router.replace("/(tabs)/tests"));
  const returning = tab === "solutions" && from && gate === "open";
  const back = () => (returning ? show("analysis") : leave());
  useEffect(() => {
    if (!returning) return;
    const sub = BackHandler.addEventListener("hardwareBackPress", () => { show("analysis"); return true; });
    return () => sub.remove();
  }, [returning, show]);
  // The phone's own back button takes the same road as the header's: an All India day's analysis goes up to the AITS Analysis list.
  useFocusEffect(useCallback(() => {
    if (fromParam !== "series-day" || returning) return;
    const sub = BackHandler.addEventListener("hardwareBackPress", () => { router.replace("/series-analysis"); return true; });
    return () => sub.remove();
  }, [fromParam, returning, router]));
  if (gate === "checking") return <View testID="result-screen" style={{ flex: 1, backgroundColor: colors.surface }} />;
  if (gate === "locked") return <ShareGate title={r?.title} stage={ready || !r ? "ready" : r.status === "embargoed" ? "sealed" : status === 202 ? "grading" : "ready"}
    onBack={leave} onOpen={() => { void unlockResult(id!); setGate("open"); }} />;
  const s = ready ? r.summary : null;
  const exam = ready ? examOf(r.exam) : null;
  // Full mocks only (the same rule recordMock uses): the Dream meter says how far each dream college is after this mock.
  const dream = exam && isFullMock({ exam: r.exam, maximum: s.maximum, questions: r.count ?? r.questions?.length, kind: r.test_kind }) ? exam : null;
  const bar = !!ready && tab === "analysis" && !!analysis.data;
  return (
    <View testID="result-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <ScreenHeader testID="result-header" backTestID="result-back-button" title={r?.title || "Result"} eyebrow={r?.exam ? `${r.exam} · ${r.test_kind === "misfire" ? "Misfire Mock" : "Result"}` : "Result"} onBack={back} />
      {ready ? (
        <View style={learningStyles.navigation}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: space.sm, paddingHorizontal: space.lg, alignItems: "center" }}>
            {TABS.map(([v, l, ic]) => <LearningTab key={v} testID={"result-tab-" + v} label={l} icon={ic} active={tab === v} onPress={() => show(v)} tone={TAB_TONE[v]} />)}
          </ScrollView>
        </View>
      ) : null}
      <KeyboardAwareScrollView ref={page as any} bottomOffset={24} keyboardShouldPersistTaps="handled" scrollEventThrottle={64}
        onScroll={e => { if (tracking.current) kept.current = e.nativeEvent.contentOffset.y; }}
        contentContainerStyle={{ padding: space.lg, paddingTop: space.sm, paddingBottom: (bar ? 0 : insets.bottom) + space.xl, gap: space.md }}>
        <ErrorBox error={err} retry={reload} testID="result-error" />
        {/* No answer yet (a weak line) or no line at all: the copy this phone keeps of this result is offered. */}
        {!r ? <KeptOffer id={id!} wait={err ? 0 : 2500} /> : null}
        {!r && !err ? <><Skeleton h={160} /><Skeleton h={120} /></> : null}
        {status === 202 && r ? <Pending r={r} id={id!} reload={reload} /> : null}
        {r?.status === "embargoed" ? <Card testID="result-embargoed"><Empty icon="lock-clock" title="Submitted · result sealed" body={`For fairness, results and solutions release at ${unixDate(r.release_at)} IST. Your receipt is safe.`} /></Card> : null}
        {ready && (r.grade_versions?.length || 0) > 0 ? (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: space.sm }}>
            <Chip testID="score-version-original" label="Original" active={version === "original"} onPress={() => setVersion("original")} />
            {r.grade_versions.map((g: any) => <Chip key={g.id} testID={"score-version-" + g.id} label={g.label || "Revised " + unixDate(g.created_at)} active={version === g.id} onPress={() => setVersion(g.id)} color={colors.custom_amber} />)}
          </ScrollView>
        ) : null}
        {ready && version !== "original" ? <Notice tone="warning" testID="score-version-note">{r.change_note || "Revised scoring version. The original result is preserved."}</Notice> : null}
        {/* A Misfire Mock made by the website: how many of its questions went to "Samajh gaya". */}
        {ready && tab === "analysis" && r.test_kind === "misfire" ? <MisfireUnderstood r={r} uid={user?.id} /> : null}
        {/* Kept in place while another tab is open, so its filters and open lists are still there on return. */}
        {ready ? <View testID="result-analysis-panel" style={tab === "analysis" ? learningStyles.panel : learningStyles.hidden}>
          <AnalysisBody id={id!} state={analysis} nav={nav} shown={tab === "analysis"} onOpen={openQuestion} onSolutions={() => show("solutions")}
            onRetry={s.incorrect || s.skipped ? () => { setRetryErr(""); setRetry("ask"); } : undefined}
            slot={dream ? <>
              <DreamMeter exam={dream} testID="result-dream" mockId={id} chart="full" onAdd={() => router.push({ pathname: "/(tabs)/rank", params: { tool: "college", at: String(Date.now()) } })} />
              <DreamCheerHost exam={dream} mockId={id} />
            </> : null} />
          {analysis.error && !analysis.data ? <Summary r={r} /> : null}
        </View> : null}
        {ready && tab === "progress" ? <Remote path={`/attempts/${id}/journey`} render={(d) => d.state !== "available" ? <Unavailable testID="progress-unavailable" title="Progress journey unavailable" reason={d.reason} /> : (
          <Card testID="progress-journey" style={[learningStyles.section, { borderTopColor: learningTones.active.line }]}>
            <T w="heavy" size={16}>Your full-mock journey</T>
            {(d.series || []).map((p: any) => <T key={p.id} size={13}>{unixDate(p.submitted_at)} · {p.title}: {p.score}/{p.maximum}</T>)}
          </Card>)} /> : null}
        {ready && tab === "confidence" ? (r.analytics?.confidence ? (
          <Card testID="confidence-card" style={[learningStyles.section, { borderTopColor: learningTones.completed.line }]}>
            <T w="heavy" size={16}>Confidence vs correctness</T>
            {Object.entries(r.analytics.confidence).filter(([, v]) => typeof v !== "object").slice(0, 8).map(([k, v]: any) => <T key={k} size={13}>{k.replace(/_/g, " ")}: {String(v)}</T>)}
          </Card>
        ) : <Unavailable testID="confidence-unavailable" title="No confidence recorded" reason="Confidence is optional. Pick “How sure are you?” before answering next time to see calibration here." />) : null}
        {ready && tab === "rank" ? <Remote path={`/attempts/${id}/historical-rank?score_version=${version}`} render={(d) => d.kind === "branch_matches" ? (
          d.state !== "available" ? <Unavailable testID="rank-unavailable" title="Branch guidance unavailable" reason={d.reason || d.limitation} /> : (
            <Card testID="bitsat-branches" style={[learningStyles.section, { borderTopColor: learningTones.saved.line }]}>
              <T w="heavy" size={16}>Top branch matches</T>
              {d.matches.map((m: any) => <T key={m.programme + m.campus} size={13}>• {m.programme} — {m.campus} (cutoff {m.cutoff}, margin {m.margin})</T>)}
              <T size={11} color={colors.muted}>{d.limitation} Admission is not guaranteed.</T>
            </Card>)
        ) : d.state !== "available" ? <Unavailable testID="rank-unavailable" title={d.label || "Reliable rank estimate unavailable"} reason={d.reason} /> : (
          <Card testID="rank-card" style={[learningStyles.section, { borderTopColor: learningTones.saved.line }]}>
            <T w="bold" size={11} color={colors.muted}>{d.label?.toUpperCase()}</T>
            <T w="heavy" size={26}>{d.rank_low?.toLocaleString("en-IN")} – {d.rank_high?.toLocaleString("en-IN")}</T>
            {d.percentile_low != null ? <T size={13}>Percentile ≈ {d.percentile_low.toFixed(2)} – {d.percentile_high.toFixed(2)}</T> : null}
            <T size={12}>{d.reason}</T>
            <T size={11} color={colors.muted}>{d.limitation}</T>
          </Card>)} /> : null}
        {ready && tab === "solutions" ? <Solutions r={r} id={id!} version={version} an={analysis.data} onAnalysis={from ? () => show("analysis") : undefined} /> : null}
      </KeyboardAwareScrollView>
      {bar ? <AnalysisBar nav={nav} inset={insets.bottom} /> : null}
      <DSheet visible={!!retry} onClose={() => { if (retry !== "busy") setRetry(""); }} testID="retry-sheet" title="Galtiyon ko revision banao">
        <T size={13.5} color={colors.custom_softText}>Ek alag attempt banega jisme sirf {(s?.incorrect || 0) + (s?.skipped || 0)} galat ya chhode hue sawaal honge. Koi timer nahi. Aapka original Score aur report nahi badlega.</T>
        <ErrorBox error={retryErr} testID="retry-error" />
        <Pill testID="retry-confirm" kind="brand" size="lg" icon="restart" label="Untimed retry shuru karo" busy={retry === "busy"} onPress={startRetry} />
        <Pill testID="retry-cancel" kind="outline" label="Abhi nahi" disabled={retry === "busy"} onPress={() => setRetry("")} />
      </DSheet>
    </View>
  );
}

const learningStyles = StyleSheet.create({
  score: { gap: space.md, borderRadius: 24, padding: 20, borderWidth: 1, borderColor: colors.brandLine },
  navigation: { minHeight: 60, paddingVertical: space.sm, justifyContent: "center" },
  panel: { gap: space.md },
  hidden: { display: "none" },
  backLink: { minHeight: 44, flexDirection: "row", alignItems: "center", gap: 6, alignSelf: "flex-start" },
  section: { gap: space.sm, borderTopWidth: 3, borderRadius: 20, paddingVertical: 20 },
  solutionTools: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", gap: space.sm, justifyContent: "space-between" },
  solutionPosition: { flex: 1, minWidth: 150, gap: 1 }, gridButton: { minHeight: 44, flexDirection: "row", alignItems: "center", gap: 6, paddingHorizontal: space.sm },
  panelCard: { gap: space.md, padding: space.lg, borderRadius: 20, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card },
  panelHead: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.sm },
  kicker: { letterSpacing: 1.7 },
  legend: { flexDirection: "row", flexWrap: "wrap", columnGap: 14, rowGap: 6, paddingTop: space.sm, borderTopWidth: 1, borderTopColor: colors.custom_barLine },
  legendItem: { flexDirection: "row", alignItems: "center", gap: 4 },
  filters: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  cardHead: { flexDirection: "row", alignItems: "flex-start", gap: space.sm },
  progress: { paddingHorizontal: space.lg, paddingTop: space.sm },
  modal: { flex: 1 },
});
