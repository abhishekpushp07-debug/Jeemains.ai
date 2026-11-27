// Taking a Misfire Mock: the same paper screen as every test (subject tabs, the question, the options, Mark for review,
// Clear, Save & Next, the palette and the submit table), with the subjects in their Student Choice colours. Every answer
// is kept on the phone at once; the clock is the mock's own deadline, so it keeps running while the app is closed.
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AppState, BackHandler, ScrollView, StyleSheet, TextInput, View, useWindowDimensions } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { imagePaths, subjectOf } from "@/src/assets/paperAssets";
import { PIECE_ZOOM, piecesOf } from "@/src/assets/pieces";
import { setPieceZoom, usePieceZoom } from "@/src/assets/pieceZoom";
import { PieceQuestion } from "@/src/components/Pieces";
import { useSubjectNavigation } from "@/src/components/player/SubjectNavigation";
import { Legend, PaletteGrid, PaletteState } from "@/src/components/player/PlayerParts";
import { AssetImage } from "@/src/components/AssetImage";
import { MathText } from "@/src/components/MathText";
import { GlossTabs } from "@/src/components/GlossTabs";
import { Icon, Notice, Press, T, tap } from "@/src/components/ui";
import { DSheet, Pill, RoundButton } from "@/src/components/design";
import { colors, fonts, radius, space } from "@/src/theme";
import { fmtClock } from "@/src/navigation";
import { SHORT, SUBJECTS, Subject } from "@/src/choice/api";
import { SUBJECT_LOOK } from "@/src/choice/looks";
import { useMockPictures } from "./pictures";
import { submit } from "./marking";
import { Answer, MARKS, Mock, latest, saveState } from "./store";

const ZOOM = [1, 1.2, 1.4];
const has = (v?: Answer) => !!String(v?.value || "").trim();
const NO: Record<string, unknown> = {};
const key = (s: Subject) => s.toLowerCase();

export function MockPlayer({ mock }: { mock: Mock }) {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const column = Math.max(1, Math.min(width, 760) - 2 * space.lg);
  const questions = mock.questions;
  const [answers, setAnswers] = useState<Record<string, Answer>>(mock.answers);
  const [visited, setVisited] = useState<string[]>(mock.visited);
  const mine = useRef({ answers, visited });
  mine.current = { answers, visited };
  const [sheet, setSheet] = useState<null | "palette" | "submit" | "exit">(null);
  const [zoom, setZoom] = useState(0);
  const pieceStep = usePieceZoom();
  const [now, setNow] = useState(Date.now());
  const reading = useRef<React.ElementRef<typeof ScrollView>>(null);
  const nav = useSubjectNavigation(questions);
  const q = nav.question;
  useMockPictures(questions, q?.id, false);

  const ended = useRef(false);
  const finish = useCallback(() => {
    if (ended.current) return;
    ended.current = true;
    submit(saveState(latest(mock), { answers: mine.current.answers, visited: mine.current.visited }));
  }, [mock]);
  const seconds = Math.max(0, Math.ceil(((mock.deadline || 0) - now) / 1000));
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    const sub = AppState.addEventListener("change", (s) => { if (s === "active") setNow(Date.now()); });
    return () => { clearInterval(t); sub.remove(); };
  }, []);
  useEffect(() => { if (mock.deadline && seconds === 0) finish(); }, [seconds, mock.deadline, finish]);
  useEffect(() => {
    const sub = BackHandler.addEventListener("hardwareBackPress", () => { setSheet("exit"); return true; });
    return () => sub.remove();
  }, []);
  useEffect(() => {
    reading.current?.scrollTo({ y: 0, animated: false });
    if (q && !mine.current.visited.includes(q.id)) {
      const next = [...mine.current.visited, q.id];
      setVisited(next);
      saveState(latest(mock), { visited: next });
    }
  }, [q?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const edit = (id: string, patch: Partial<Answer>) => {
    if (ended.current || seconds === 0) return;
    const next = { ...mine.current.answers, [id]: { ...(mine.current.answers[id] || { value: "" }), ...patch } };
    setAnswers(next);
    mine.current = { ...mine.current, answers: next };
    saveState(latest(mock), { answers: next });
  };

  const subjects = useMemo(() => SUBJECTS.filter((s) => questions.some((x) => x.subject === s)), [questions]);
  if (!q) return null;
  const cur = answers[q.id] || { value: "", marked: false };
  const timeUp = seconds === 0;
  const disabled = timeUp;
  const stateOf = (x: { id: string }): PaletteState => {
    const v = answers[x.id];
    if (has(v)) return v?.marked ? "answered_marked" : "answered";
    if (v?.marked) return "marked";
    if (x.id === q.id || visited.includes(x.id)) return "not_answered";
    return "fresh";
  };
  const answeredOf = (x: { id: string }) => has(answers[x.id]);
  const counts = { answered: questions.filter(answeredOf).length, marked: questions.filter((x) => answers[x.id]?.marked).length };
  const idx = nav.index;
  const go = (d: number) => { const n = nav.rows[idx + d]; if (n) { tap(); nav.select(n.id); } };
  const nextSubject = nav.subjects[nav.subjects.indexOf(nav.subject) + 1];
  const subjectCounts = nav.rows.reduce((c, x) => { c[stateOf(x)]++; return c; }, { answered: 0, answered_marked: 0, marked: 0, not_answered: 0, fresh: 0 } as Record<PaletteState, number>);
  const timerTone = seconds <= 120 ? colors.custom_qNotAnswered : seconds <= 600 ? colors.custom_timerAmber : colors.onSurface;
  const pieces = piecesOf(q);
  const scale = pieces ? PIECE_ZOOM[pieceStep] : ZOOM[zoom];
  const largest = pieces ? pieceStep === PIECE_ZOOM.length - 1 : zoom === ZOOM.length - 1;
  const nextZoom = () => (pieces ? setPieceZoom((pieceStep + 1) % PIECE_ZOOM.length) : setZoom((z) => (z + 1) % ZOOM.length));
  const pick = (k: string) => edit(q.id, { value: cur.value === k ? "" : k });
  const source = q.render_mode === "source";
  const labels = q.source_option_labels || null, typed = q.typed_options || {};
  const optionKeys = Object.keys(q.options || {});
  const numeric = !optionKeys.length;
  const optionTiles = source && !numeric && !Object.keys(typed).length;
  const labelOf = (k: string) => labels?.[k] || k;
  const sourceHint = Object.keys(typed).length ? "Read the options in the picture above. Options the picture does not show are typed below."
    : `Read options ${labelOf(optionKeys[0] || "A")}–${labelOf(optionKeys[optionKeys.length - 1] || "D")} in the picture above, then tap the matching ${labels ? "number" : "letter"}.`;
  const narrow = width < 380;
  const primary = idx < nav.rows.length - 1
    ? { testID: "mock-next-button", label: "Save & Next", onPress: () => go(1) }
    : nextSubject ? { testID: "mock-next-subject", label: `Next: ${SHORT[nextSubject as Subject] || nextSubject}`, onPress: () => nav.selectSubject(nextSubject) }
      : { testID: "mock-open-submit", label: narrow ? "Submit" : "Review & submit", onPress: () => setSheet("submit") };
  const tabs = (prefix: string) => <GlossTabs prefix={prefix} value={key(nav.subject as Subject)} onChange={(k) => { const s = subjects.find((x) => key(x) === k); if (s) nav.selectSubject(s); }}
    items={subjects.map((s) => { const rows = questions.filter((x) => x.subject === s); return { key: key(s), label: SHORT[s], look: SUBJECT_LOOK[s], sub: `${rows.filter(answeredOf).length}/${rows.length}`, subTestID: `${prefix}-${key(s)}-count` }; })} />;

  return <View testID="mock-player-screen" style={{ flex: 1, backgroundColor: colors.surface }}>
    <View style={[styles.top, { paddingTop: insets.top + space.sm }]}>
      <View style={styles.topRow}>
        <RoundButton testID="mock-exit-button" icon="close" label="Leave mock" color={colors.onSurface} onPress={() => setSheet("exit")} />
        <View style={{ flex: 1, minWidth: 0 }}>
          <T w="heavy" size={13.5} numberOfLines={1}>{mock.title}</T>
          <View style={styles.saveRow}><View style={[styles.saveDot, { backgroundColor: colors.custom_mint }]} /><T testID="mock-save-label" w="bold" size={10.5} color={colors.custom_mint} numberOfLines={1}>Saved on phone</T></View>
        </View>
        <View testID="mock-timer" accessibilityLabel={`Time left ${fmtClock(seconds)}`} style={[styles.timer, seconds <= 600 && { borderColor: timerTone }]}>
          <Icon name="clock-outline" size={15} color={timerTone} />
          <T testID="mock-timer-label" w="heavy" size={14} color={timerTone} style={{ fontVariant: ["tabular-nums"], letterSpacing: 0.4 }}>{fmtClock(seconds)}</T>
        </View>
        <Press testID="mock-submit-top" onPress={() => setSheet("submit")} accessibilityLabel="Submit mock" style={styles.submitTop}>
          <T w="heavy" size={12} color={colors.onBrandPrimary}>Submit</T>
        </Press>
      </View>
      <View testID="mock-progress" style={styles.progress} accessibilityLabel={`${counts.answered} of ${questions.length} answered`}>
        <LinearGradient colors={[colors.brandPrimary, colors.custom_todayTo]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={{ width: `${(counts.answered / Math.max(1, questions.length)) * 100}%`, height: "100%", borderRadius: 2 }} />
      </View>
      {tabs("mock-subject")}
    </View>

    <ScrollView ref={reading} style={{ flex: 1 }} contentContainerStyle={styles.page} keyboardShouldPersistTaps="handled">
      {timeUp ? <Notice tone="error" testID="mock-time-up">Time’s up. Your answers are being marked.</Notice> : null}
      <View style={styles.qHead}>
        <View style={{ flex: 1, gap: 8 }}>
          <T testID="mock-position" w="heavy" size={22} accessibilityLabel={`${subjectOf(q)}, question ${q.number} of ${questions.length}`}>Q {q.number}<T w="semibold" size={14} color={colors.custom_eyebrow}> of {questions.length}</T></T>
          <View style={styles.tags}>
            <View style={styles.tag}><T w="heavy" size={9} color={colors.muted} style={{ letterSpacing: 1.2 }}>{numeric ? "NUMERICAL" : "SINGLE CORRECT"}</T></View>
            <View testID="mock-marking" style={styles.tag}><T w="heavy" size={10} color={colors.muted}>+{MARKS.correct} · −{Math.abs(MARKS.wrong)}</T></View>
          </View>
        </View>
        <RoundButton testID="mock-prev-button" icon="chevron-left" label="Previous question" onPress={() => go(-1)} style={idx <= 0 ? { opacity: 0.4 } : undefined} />
        <RoundButton testID="mock-star-button" icon={cur.marked ? "star" : "star-outline"} color={cur.marked ? colors.custom_qMarkedInk : colors.custom_gold} label={cur.marked ? "Unmark review" : "Mark for review"} active={!!cur.marked} onPress={() => edit(q.id, { marked: !cur.marked })} />
        <RoundButton testID="mock-zoom-button" icon={largest ? "magnify-minus-outline" : "magnify-plus-outline"} label={`Text size ${Math.round(scale * 100)}%`} onPress={nextZoom} />
      </View>

      {pieces ? <PieceQuestion id={q.attempt_id} q={q} width={column} testPrefix="mock" value={cur.value} onPick={pick} disabled={disabled} /> : (
        <View testID="mock-question" style={styles.question}>
          {!source && q.text ? <MathText testID="mock-question-text" size={Math.round(16 * scale)} text={q.text} /> : null}
          {imagePaths(q.attempt_id, q, "question").map((path, i) => <AssetImage key={path} testID={`mock-question-image-${q.number}-${i}`} path={path} label={(source && q.accessible_text) || `Question ${q.number}`} />)}
        </View>
      )}
      {!numeric && source && !pieces ? <T testID="mock-source-hint" size={12.5} color={colors.muted}>{sourceHint}</T> : null}
      {numeric ? <View style={{ gap: 6 }}>
        <T w="heavy" size={10} color={colors.custom_eyebrow} style={{ letterSpacing: 1.8 }}>YOUR ANSWER</T>
        <TextInput testID="mock-integer-input" editable={!disabled} value={cur.value} onChangeText={(v) => edit(q.id, { value: v.slice(0, 30) })} keyboardType="numbers-and-punctuation" placeholder="Type an exact integer"
          placeholderTextColor={colors.custom_dim} style={[styles.numeric, has(cur) && { borderColor: colors.onSurface }]} />
      </View> : pieces ? null : optionTiles ? <View testID="mock-option-tiles" style={styles.tiles}>
        {optionKeys.map((k) => { const sel = cur.value === k; return <Press key={k} testID={`mock-option-${k}`} disabled={disabled} onPress={() => pick(k)} scaleTo={0.96}
          accessibilityLabel={`Option ${labelOf(k)}, as shown in the picture${sel ? ", selected" : ""}`} accessibilityState={{ selected: sel }} style={[styles.tile, sel && styles.tileOn]}>
          <T w="mono" size={Math.round(24 * scale)} color={sel ? colors.custom_pickInk : colors.onSurface}>{labelOf(k)}</T>
          {sel ? <View style={styles.tileCheck}><Icon name="check" size={11} color={colors.onSuccess} /></View> : null}
        </Press>; })}
      </View> : <View style={{ gap: 10 }}>
        {optionKeys.map((k) => {
          const sel = cur.value === k, label = String(q.options?.[k] ?? "");
          const text = source ? typed[k] || `Option ${labelOf(k)} (as shown above)` : label.startsWith("See original") ? `Option ${k} (see image)` : label;
          return <Press key={k} testID={`mock-option-${k}`} disabled={disabled} onPress={() => pick(k)} accessibilityLabel={`Option ${labelOf(k)}${sel ? ", selected" : ""}`} accessibilityState={{ selected: sel }} scaleTo={0.985} style={[styles.option, sel && styles.optionOn]}>
            <View style={[styles.letter, sel && styles.letterOn]}><T w="heavy" size={13} color={sel ? colors.onSuccess : colors.custom_softText}>{labelOf(k)}</T></View>
            {source && typed[k] ? <View style={{ flex: 1 }}><MathText testID={`mock-option-math-${k}`} size={Math.round(15 * scale)} text={typed[k]} /></View>
              : <T size={Math.round(15 * scale)} w={sel ? "heavy" : "medium"} style={{ flex: 1 }} color={sel ? colors.onSurface : colors.custom_softText}>{text}</T>}
            {sel ? <View style={styles.check}><Icon name="check" size={14} color={colors.onSuccess} /></View> : null}
          </Press>;
        })}
      </View>}
    </ScrollView>

    <View style={[styles.dock, { paddingBottom: insets.bottom + space.sm }]}>
      <View style={styles.dockRow}>
        <Press testID="mock-mark-button" disabled={disabled} onPress={() => edit(q.id, { marked: !cur.marked })} accessibilityLabel={cur.marked ? "Unmark review" : "Mark for review"} accessibilityState={{ selected: !!cur.marked }}
          style={[styles.mark, cur.marked && { backgroundColor: colors.custom_qMarkedSoft }]}>
          <Icon name={cur.marked ? "flag" : "flag-outline"} size={17} color={colors.custom_qMarkedInk} />
          <T w="heavy" size={12.5} numberOfLines={1} color={colors.custom_qMarkedInk}>{cur.marked ? "Marked" : narrow ? "Review" : "Mark for review"}</T>
        </Press>
        <Press testID="mock-clear-button" disabled={disabled || !has(cur)} onPress={() => edit(q.id, { value: "" })} accessibilityLabel="Clear response" style={styles.clear}>
          <T w="bold" size={12.5} color={colors.custom_softText}>Clear</T>
        </Press>
        <Press testID={primary.testID} onPress={primary.onPress} accessibilityLabel={primary.label} style={styles.next}>
          <T w="heavy" size={13.5} numberOfLines={1} color={colors.custom_bar}>{primary.label}</T>
          <Icon name="arrow-right" size={17} color={colors.custom_bar} />
        </Press>
      </View>
      <View style={styles.summary}>
        <View style={styles.summaryCounts}>
          <Count color={colors.custom_qAnswered} label={`${counts.answered} answered`} testID="mock-count-answered" />
          <Count color={colors.custom_qMarked} label={`${counts.marked} marked`} testID="mock-count-marked" />
          <Count color={colors.custom_qFreshLine} label={`${questions.length - counts.answered} left`} testID="mock-count-left" />
        </View>
        <Press testID="mock-palette-button" onPress={() => setSheet("palette")} accessibilityLabel="Question palette" style={styles.paletteBtn}>
          <Icon name="view-grid" size={14} color={colors.onSurface} /><T w="heavy" size={12}>Palette</T>
        </Press>
      </View>
    </View>

    <DSheet visible={sheet === "palette"} onClose={() => setSheet(null)} testID="mock-palette-sheet" title="Question palette" closeTestID="mock-palette-close">
      {tabs("mock-palette-subject")}
      <Legend counts={subjectCounts} pending={0} />
      <T w="heavy" size={10} color={colors.custom_eyebrow} style={{ letterSpacing: 1.8 }}>{(SHORT[nav.subject as Subject] || nav.subject).toUpperCase()} · {nav.rows.length} QUESTIONS</T>
      <PaletteGrid prefix="mock-palette-q" questions={nav.rows} stateOf={stateOf} currentId={q.id} pendingIds={NO} onSelect={(qid) => { nav.select(qid); setSheet(null); }} />
      <View style={styles.sheetActions}>
        <Pill testID="mock-palette-back" kind="outline" label={narrow ? "Back" : "Back to question"} onPress={() => setSheet(null)} style={{ flex: 1 }} />
        <Pill testID="mock-palette-submit" kind="brand" label="Submit mock" onPress={() => setSheet("submit")} style={{ flex: 1 }} />
      </View>
    </DSheet>

    <DSheet visible={sheet === "submit"} onClose={() => setSheet(null)} testID="mock-submit-sheet" title="Submit mock?">
      <View testID="mock-submit-summary" style={styles.table}>
        <View style={styles.tableRow}>
          <T w="heavy" size={10} color={colors.custom_eyebrow} style={styles.tableName}>SUBJECT</T>
          {["DONE", "MARKED", "LEFT"].map((h) => <T key={h} w="heavy" size={10} color={colors.custom_eyebrow} style={styles.tableNum}>{h}</T>)}
        </View>
        {subjects.map((s) => {
          const rows = questions.filter((x) => x.subject === s), done = rows.filter(answeredOf).length, marked = rows.filter((x) => answers[x.id]?.marked).length;
          return <View key={s} testID={`mock-submit-${key(s)}`} style={[styles.tableRow, styles.tableLine]}>
            <T w="bold" size={13} style={styles.tableName} numberOfLines={1}>{SHORT[s]}</T>
            <T w="heavy" size={14} color={colors.custom_qAnswered} style={styles.tableNum}>{done}</T>
            <T w="heavy" size={14} color={colors.custom_qMarkedInk} style={styles.tableNum}>{marked}</T>
            <T w="heavy" size={14} color={colors.custom_qNotAnswered} style={styles.tableNum}>{rows.length - done}</T>
          </View>;
        })}
        <View style={[styles.tableRow, styles.tableLine]}>
          <T w="heavy" size={13} style={styles.tableName}>Total · {questions.length}</T>
          <T testID="mock-submit-answered" w="heavy" size={14} style={styles.tableNum}>{counts.answered}</T>
          <T w="heavy" size={14} style={styles.tableNum}>{counts.marked}</T>
          <T w="heavy" size={14} style={styles.tableNum}>{questions.length - counts.answered}</T>
        </View>
      </View>
      <T size={12} color={colors.custom_eyebrow}>Submit ke baad jawab nahi badlenge. Result aur solutions turant milenge.</T>
      <Pill testID="mock-confirm-submit" kind="brand" size="lg" label="Submit now" onPress={() => { setSheet(null); finish(); }} />
      <Pill testID="mock-cancel-submit" kind="outline" label="Keep working" onPress={() => setSheet(null)} />
    </DSheet>

    <DSheet visible={sheet === "exit"} onClose={() => setSheet(null)} testID="mock-exit-sheet" title="Leave this mock?">
      <T size={13} color={colors.muted}>Kuch submit nahi hoga. Timer chalta rahega; My Tests ya Misfire se isi mock par wapas aa sakte ho. Aapke jawab phone par safe hain.</T>
      <Pill testID="mock-exit-stay" label="Stay" onPress={() => setSheet(null)} />
      <Pill testID="mock-exit-confirm" kind="outline" label="Leave (keep mock)" onPress={() => { setSheet(null); if (router.canGoBack()) router.back(); else router.replace({ pathname: "/misfire", params: { tab: "mock" } } as any); }} />
    </DSheet>
  </View>;
}

function Count({ color, label, testID }: { color: string; label: string; testID: string }) {
  return <View testID={testID} style={styles.count}><View style={[styles.countDot, { backgroundColor: color }]} /><T w="bold" size={11} color={colors.custom_softText} numberOfLines={1}>{label}</T></View>;
}

const styles = StyleSheet.create({
  top: { paddingHorizontal: space.lg, paddingBottom: space.sm, gap: space.md, backgroundColor: colors.surface },
  topRow: { flexDirection: "row", alignItems: "center", gap: space.sm },
  saveRow: { flexDirection: "row", alignItems: "center", gap: 5, marginTop: 2 },
  saveDot: { width: 7, height: 7, borderRadius: 4 },
  timer: { flexDirection: "row", alignItems: "center", gap: 5, paddingHorizontal: 12, height: 40, borderRadius: radius.pill, backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLineStrong },
  submitTop: { height: 40, minWidth: 44, paddingHorizontal: 14, borderRadius: radius.pill, backgroundColor: colors.brandPrimary, alignItems: "center", justifyContent: "center" },
  progress: { height: 4, borderRadius: 2, backgroundColor: colors.custom_barLine, overflow: "hidden" },
  page: { paddingHorizontal: space.lg, paddingTop: space.md, gap: space.md, paddingBottom: space.xl, width: "100%", maxWidth: 760, alignSelf: "center" },
  qHead: { flexDirection: "row", alignItems: "flex-start", gap: 6 },
  tags: { flexDirection: "row", gap: 6, flexWrap: "wrap" },
  tag: { height: 22, paddingHorizontal: 10, borderRadius: 11, backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLineStrong, justifyContent: "center" },
  question: { backgroundColor: colors.custom_card, borderRadius: 20, borderWidth: 1, borderColor: colors.custom_cardLine, padding: 18, gap: space.md },
  numeric: { height: 64, borderRadius: 16, borderWidth: 1.5, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, paddingHorizontal: space.lg, fontFamily: fonts.heavy, fontSize: 24, color: colors.onSurface },
  option: { flexDirection: "row", alignItems: "center", gap: 14, minHeight: 60, paddingHorizontal: space.lg, paddingVertical: space.md, borderRadius: 16, borderWidth: 1.5, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card },
  optionOn: { borderWidth: 2, borderColor: colors.custom_pickLine, backgroundColor: colors.custom_pickWash, paddingHorizontal: space.lg - 0.5 },
  letter: { width: 30, height: 30, borderRadius: 15, borderWidth: 1.5, borderColor: colors.custom_qFreshLine, alignItems: "center", justifyContent: "center" },
  letterOn: { backgroundColor: colors.custom_pick, borderColor: colors.custom_pick },
  check: { width: 22, height: 22, borderRadius: 11, backgroundColor: colors.custom_pick, alignItems: "center", justifyContent: "center" },
  tiles: { flexDirection: "row", gap: space.sm },
  tile: { flex: 1, minWidth: 0, height: 68, borderRadius: 18, borderWidth: 1.5, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, alignItems: "center", justifyContent: "center" },
  tileOn: { borderWidth: 2, backgroundColor: colors.custom_pickWash, borderColor: colors.custom_pickLine },
  tileCheck: { position: "absolute", top: 6, right: 6, width: 16, height: 16, borderRadius: 8, backgroundColor: colors.custom_pick, alignItems: "center", justifyContent: "center" },
  dock: { backgroundColor: colors.custom_bar, borderTopWidth: 1, borderTopColor: colors.custom_barLine, paddingHorizontal: space.lg, paddingTop: space.md, gap: space.sm },
  dockRow: { flexDirection: "row", gap: space.sm, width: "100%", maxWidth: 760, alignSelf: "center" },
  mark: { flex: 1.15, minWidth: 0, height: 48, borderRadius: radius.pill, borderWidth: 1.5, borderColor: colors.custom_qMarked, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 5, paddingHorizontal: 8 },
  clear: { width: 64, height: 48, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, alignItems: "center", justifyContent: "center" },
  next: { flex: 1.1, minWidth: 0, height: 48, borderRadius: radius.pill, backgroundColor: colors.onSurface, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 5, paddingHorizontal: 8 },
  summary: { flexDirection: "row", alignItems: "center", gap: space.sm, width: "100%", maxWidth: 760, alignSelf: "center" },
  summaryCounts: { flex: 1, flexDirection: "row", flexWrap: "wrap", columnGap: 12, rowGap: 2 },
  count: { flexDirection: "row", alignItems: "center", gap: 5 },
  countDot: { width: 9, height: 9, borderRadius: 5 },
  paletteBtn: { flexDirection: "row", alignItems: "center", gap: 6, height: 44, paddingHorizontal: 14, borderRadius: radius.pill, backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLineStrong },
  sheetActions: { flexDirection: "row", gap: space.sm },
  table: { borderRadius: 16, backgroundColor: colors.custom_bar, borderWidth: 1, borderColor: colors.custom_barLine, paddingHorizontal: space.md, paddingVertical: space.sm },
  tableRow: { flexDirection: "row", alignItems: "center", minHeight: 36 },
  tableLine: { borderTopWidth: 1, borderTopColor: colors.custom_barLine },
  tableName: { flex: 1.4, letterSpacing: 0.4 },
  tableNum: { flex: 1, textAlign: "center" },
});
