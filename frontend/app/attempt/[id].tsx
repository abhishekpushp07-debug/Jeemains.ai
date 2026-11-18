import React, { useEffect, useMemo, useRef, useState } from "react";
import { BackHandler, ScrollView, StyleSheet, TextInput, View, useWindowDimensions } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { useAuth } from "@/src/auth";
import { useAttempt } from "@/src/useAttempt";
import { availableQuestions, imagePaths, subjectId, subjectOf, usePaperAssets } from "@/src/assets/paperAssets";
import { useSubjectNavigation } from "@/src/components/player/SubjectNavigation";
import { Legend, PaletteGrid, PaletteState, SubjectSegment, shortSubject } from "@/src/components/player/PlayerParts";
import { invalidate } from "@/src/useCached";
import { AssetImage } from "@/src/components/AssetImage";
import { ImageWarmup } from "@/src/components/player/ImageWarmup";
import { MathText } from "@/src/components/MathText";
import { ErrorBox, Icon, Notice, Press, Skeleton, T, tap } from "@/src/components/ui";
import { DSheet, Pill, RoundButton } from "@/src/components/design";
import { colors, fonts, radius, space } from "@/src/theme";
import { fmtClock } from "@/src/navigation";
import { lockResult } from "@/src/mission/gate";

const CONF = [[0.25, "Guess"], [0.5, "Unsure"], [1, "Sure"]] as const;
const ZOOM = [1, 1.2, 1.4];
const has = (v: any) => !!String(v?.value || "").trim();
// Tablets: a centred reading column; wide screens (landscape tablets) add an always-open palette panel.
const TABLET = 600, WIDE = 900, COLUMN = 760, SIDE = 360;

export default function Player() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { user } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  // Only a submission made here (the attempt was open on this screen) locks its result behind the share card;
  // opening an attempt that was already finished goes straight to its result.
  const wasActive = useRef(false);
  const toResult = () => {
    invalidate(`u.${user?.id}.`);
    const go = () => router.replace(`/result/${id}`);
    if (wasActive.current) void lockResult(id!).finally(go); else go();
  };
  const A = useAttempt(id!, user?.id || "anon", toResult);
  const a = A.attempt;
  useEffect(() => { if (a?.status === "active") wasActive.current = true; }, [a?.status]);
  const [sheet, setSheet] = useState<null | "palette" | "submit" | "exit" | "bonus">(null);
  const [busy, setBusy] = useState(false);
  const [conf, setConf] = useState<Record<string, number | undefined>>({});
  const [zoom, setZoom] = useState(0);
  const reading = useRef<React.ElementRef<typeof ScrollView>>(null);

  const bonusRule = a?.rules?.bonus_rule;
  const bonusOpen = !!a?.bonus_unlocked_at;
  const questions = useMemo(() => availableQuestions<any>(a?.questions || [], bonusOpen), [a?.questions, bonusOpen]);
  const nav = useSubjectNavigation<any>(questions);
  const q = nav.question;
  const warmPaths = usePaperAssets(id!, questions, q?.id, false);
  useEffect(() => { if (q) A.visit(q.id); }, [q?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    reading.current?.scrollTo({ y: 0, animated: false });
  }, [q?.id]);
  useEffect(() => {
    const sub = BackHandler.addEventListener("hardwareBackPress", () => { setSheet("exit"); return true; });
    return () => sub.remove();
  }, []);

  if (!a || !q) return (
    <View style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.lg, padding: space.lg, gap: space.md }}>
      <T w="heavy" size={18}>Opening your attempt…</T>
      <ErrorBox error={A.error || (a ? "No available questions were returned for this attempt." : "")} retry={A.load} testID="player-load-error" />
      {!A.error ? <><Skeleton h={60} /><Skeleton h={260} /></> : <Pill testID="player-back-button" kind="outline" label="Back" onPress={() => router.back()} />}
    </View>
  );

  const answer = (x: any) => A.pending[x.id] || a.answers?.[x.id];
  const stateOf = (x: any): PaletteState => {
    const v = answer(x);
    if (has(v)) return v?.marked ? "answered_marked" : "answered";
    if (v?.marked) return "marked";
    if (x.id === q.id || A.pending[x.id] || a.visited?.includes(x.id)) return "not_answered";
    return "fresh";
  };
  const cur = answer(q) || { value: "", marked: false };
  const lockedMain = bonusOpen && !q?.bonus;
  const timeUp = A.seconds === 0;
  // Options stay open while a question image is still loading: a slow image must never stop a student from answering.
  const disabled = timeUp || A.conflict || lockedMain;
  const pendingCount = Object.keys(A.pending).length;
  const saveState = A.conflict ? ["Conflict", colors.error] : !A.online ? ["Offline", colors.error] : A.inflight ? ["Saving…", colors.info] : pendingCount ? [`${pendingCount} pending`, colors.warning] : ["Saved", colors.custom_mint];
  const idx = nav.index;
  const go = (d: number) => { const n = nav.rows[idx + d]; if (n) { tap(); nav.select(n.id); } };
  const nextSubject = nav.subjects[nav.subjects.indexOf(nav.subject) + 1];
  const answeredOf = (x: any) => has(answer(x));
  const counts = { answered: questions.filter(answeredOf).length, marked: questions.filter((x: any) => answer(x)?.marked).length, pending: pendingCount };
  const bonusEligible = bonusRule && !bonusOpen && (a.questions || []).filter((x: any) => !x.bonus).every((x: any) => has(answer(x)));
  const rule = q.scoring || a.rules || {};
  const marking = rule.correct != null ? `+${rule.correct} · ${Number(rule.wrong) < 0 ? "−" + Math.abs(rule.wrong) : rule.wrong ?? 0}` : "";
  const seconds = A.seconds ?? 99999;
  const timerTone = seconds <= 120 ? colors.custom_qNotAnswered : seconds <= 600 ? colors.custom_timerAmber : colors.onSurface;
  const scale = ZOOM[zoom];
  const subjectCounts = nav.rows.reduce((c, x: any) => { c[stateOf(x)]++; return c; }, { answered: 0, answered_marked: 0, marked: 0, not_answered: 0, fresh: 0 } as Record<PaletteState, number>);
  const subjectPending = nav.rows.filter((x: any) => A.pending[x.id]).length;
  const wide = width >= WIDE;
  const frame = width >= TABLET ? styles.frame : null;
  const topFrame = wide ? null : frame;
  const readWidth = wide ? Math.min(width - SIDE, COLUMN) : Math.min(width, COLUMN);

  async function doSubmit() {
    setBusy(true);
    try {
      await A.submit();
      toResult();
    } catch (e: any) {
      A.setError(e.message);
      setBusy(false);
    }
  }
  async function doBonus() {
    setBusy(true);
    try { await A.enterBonus(); setSheet(null); } catch (e: any) { A.setError(e.message); }
    setBusy(false);
  }

  const primary = idx < nav.rows.length - 1
    ? { testID: "player-next-button", label: "Save & Next", onPress: () => go(1), a11y: "Save and go to next question" }
    : nextSubject ? { testID: "player-next-subject", label: `Next: ${shortSubject(nextSubject)}`, onPress: () => nav.selectSubject(nextSubject), a11y: `Continue to ${nextSubject}` }
      : { testID: "player-open-submit", label: "Review & submit", onPress: () => setSheet("submit"), a11y: "Review and submit" };

  return (
    <View testID="player-screen" style={{ flex: 1, backgroundColor: colors.surface }}>
      <ImageWarmup paths={warmPaths} width={Math.max(1, readWidth - 2 * space.lg - 2 * 18 - 2)} />
      <View style={[styles.top, { paddingTop: insets.top + space.sm }]}>
        <View style={[styles.topRow, topFrame]}>
          <RoundButton testID="player-exit-button" icon="close" label="Leave attempt" color={colors.onSurface} onPress={() => setSheet("exit")} />
          <View style={{ flex: 1, minWidth: 0 }}>
            <T w="heavy" size={13.5} numberOfLines={1}>{a.title}</T>
            <View testID="player-save-status" style={styles.saveRow} accessibilityLiveRegion="polite">
              <View style={[styles.saveDot, { backgroundColor: saveState[1] }]} />
              <T w="bold" size={10.5} color={saveState[1]}>{saveState[0]}</T>
            </View>
          </View>
          {a.deadline ? (
            <View testID="player-timer" accessibilityLabel={`Time left ${fmtClock(A.seconds ?? 0)}`} style={[styles.timer, seconds <= 600 && { borderColor: timerTone }]}>
              <Icon name="clock-outline" size={15} color={timerTone} />
              <T w="heavy" size={14} color={timerTone} style={{ fontVariant: ["tabular-nums"], letterSpacing: 0.4 }}>{fmtClock(A.seconds ?? 0)}</T>
            </View>
          ) : <T size={11} w="bold" color={colors.custom_eyebrow}>Untimed</T>}
          <Press testID="player-submit-top" onPress={() => setSheet("submit")} accessibilityLabel="Submit test" style={styles.submitTop}>
            <T w="heavy" size={12} color={colors.onBrandPrimary}>Submit</T>
          </Press>
        </View>
        <View testID="player-progress" style={[styles.progress, topFrame]} accessibilityLabel={`${counts.answered} of ${questions.length} answered`}>
          <LinearGradient colors={[colors.brandPrimary, colors.custom_todayTo]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={{ width: `${(counts.answered / Math.max(1, questions.length)) * 100}%`, height: "100%", borderRadius: 2 }} />
        </View>
        <View style={topFrame}><SubjectSegment prefix="player-subject" questions={questions} subject={nav.subject} onSelect={nav.selectSubject} answered={answeredOf} /></View>
      </View>

      <View style={styles.body}>
      <View style={{ flex: 1 }}>
      <ScrollView ref={reading} style={{ flex: 1 }} contentContainerStyle={[{ paddingHorizontal: space.lg, paddingTop: space.md, gap: space.md, paddingBottom: space.xl }, frame]} keyboardShouldPersistTaps="handled">
        {timeUp ? <Notice tone="error" testID="player-time-up">Time’s up. Editing is closed; confirming the sealed attempt with the server. Late drafts are not scored.</Notice> : null}
        {A.conflict ? (
          <Notice tone="error" testID="player-conflict">
            <T size={13} w="medium" color={colors.error}>A newer answer exists on the server (another device or session). Your pending drafts are kept, not overwritten.</T>
            <View style={{ flexDirection: "row", gap: space.sm, marginTop: 6 }}>
              <Press testID="conflict-reload" onPress={A.load}><T w="bold" size={13} color={colors.brandText}>View server version</T></Press>
              <Press testID="conflict-discard" onPress={A.discard}><T w="bold" size={13} color={colors.error}>Discard my drafts</T></Press>
            </View>
          </Notice>
        ) : null}
        {A.error && !A.conflict ? <ErrorBox error={A.error} testID="player-error" /> : null}
        {lockedMain ? <Notice tone="info">Main answers are locked after entering the bonus section.</Notice> : null}

        <View style={styles.qHead}>
          <View style={{ flex: 1, gap: 8 }}>
            <T testID="player-subject-position" w="heavy" size={22} accessibilityLabel={`${nav.subject}, question ${q.number} of ${questions.length}`}>Q {q.number}<T w="semibold" size={14} color={colors.custom_eyebrow}> of {questions.length}</T></T>
            <View style={styles.tags}>
              <View style={styles.tag}><T w="heavy" size={9} color={colors.muted} style={{ letterSpacing: 1.2 }}>{q.type === "integer" ? "NUMERICAL" : "SINGLE CORRECT"}{q.bonus ? " · BONUS" : ""}</T></View>
              {marking ? <View testID="player-marking" style={styles.tag}><T w="heavy" size={10} color={colors.muted}>{marking}</T></View> : null}
            </View>
          </View>
          <RoundButton testID="player-prev-button" icon="chevron-left" label="Previous question" onPress={() => go(-1)} style={idx <= 0 ? { opacity: 0.4 } : undefined} />
          <RoundButton testID="player-star-button" icon={cur.marked ? "star" : "star-outline"} color={cur.marked ? colors.custom_qMarkedInk : colors.custom_gold} label={cur.marked ? "Unmark review" : "Mark for review"} active={!!cur.marked} onPress={() => { if (!disabled) A.edit(q.id, { marked: !cur.marked }); }} />
          <RoundButton testID="player-zoom-button" icon={zoom === ZOOM.length - 1 ? "magnify-minus-outline" : "magnify-plus-outline"} label={`Text size ${Math.round(scale * 100)}%`} onPress={() => setZoom(z => (z + 1) % ZOOM.length)} />
        </View>

        <View testID="question-reading-surface" style={styles.question}>
          {q.render_mode !== "source" && q.text ? <MathText testID="player-question-text" size={Math.round(16 * scale)} text={q.text} /> : null}
          {imagePaths(id!, q, "question").map((path, i) => (
            <AssetImage key={path} testID={`question-image-${q.number}-${i}`} path={path} label={`Question ${q.number} original image`} />
          ))}
          {q.render_mode === "source" && q.text ? <T size={11} color={colors.custom_eyebrow}>{q.text}</T> : null}
        </View>

        {q.type === "integer" ? (
          <View style={{ gap: 6 }}>
            <T w="heavy" size={10} color={colors.custom_eyebrow} style={{ letterSpacing: 1.8 }}>YOUR ANSWER</T>
            <TextInput testID="player-integer-input" editable={!disabled} value={cur.value} onChangeText={(v) => A.edit(q.id, { value: v.slice(0, 30) })} keyboardType="numbers-and-punctuation" placeholder="Type an exact integer"
              placeholderTextColor={colors.custom_dim} style={[styles.numeric, has(cur) && { borderColor: colors.onSurface }]} />
          </View>
        ) : (
          <View style={{ gap: 10 }}>
            {Object.entries(q.options || {}).map(([k, label]) => {
              const sel = cur.value === k;
              return (
                <Press key={k} testID={`player-option-${k}`} disabled={disabled} onPress={() => {
                    // Exam mode: the student moves on with Save & Next (review, confidence and changes stay possible).
                    A.edit(q.id, { value: sel ? "" : k, ...(conf[q.id] != null ? { confidence: conf[q.id] } : {}) });
                  }} accessibilityLabel={`Option ${k}${sel ? ", selected" : ""}`} accessibilityState={{ selected: sel }} scaleTo={0.985}
                  style={[styles.option, sel && styles.optionOn]}>
                  <View style={[styles.letter, sel && styles.letterOn]}>
                    <T w="heavy" size={13} color={sel ? colors.onSurfaceInverse : colors.custom_softText}>{k}</T>
                  </View>
                  <T size={Math.round(15 * scale)} w={sel ? "heavy" : "medium"} style={{ flex: 1 }} color={sel ? colors.onSurface : colors.custom_softText}>{String(label).startsWith("See original") ? `Option ${k} (see image)` : String(label)}</T>
                  {sel ? <View style={styles.check}><Icon name="check" size={14} color={colors.onSurfaceInverse} /></View> : null}
                </Press>
              );
            })}
          </View>
        )}

        {!a.confidence_observations?.[q.id] ? (
          <View testID="player-confidence" style={styles.conf}>
            <T size={11} color={colors.custom_eyebrow}>How sure?</T>
            {CONF.map(([v, l]) => {
              const on = conf[q.id] === v;
              return <Press key={l} testID={"confidence-" + v} accessibilityState={{ selected: on }} accessibilityLabel={`Confidence: ${l}`} onPress={() => {
                const nv = on ? undefined : v;
                setConf((c) => ({ ...c, [q.id]: nv }));
                // Already answered: save confidence right away with the existing answer.
                if (nv != null && has(cur)) A.edit(q.id, { value: cur.value, confidence: nv });
              }} style={[styles.confChip, on && styles.confOn]}>
                <T w={on ? "heavy" : "bold"} size={11.5} color={on ? colors.custom_mint : colors.muted}>{l}</T>
              </Press>;
            })}
          </View>
        ) : null}
      </ScrollView>

      <View style={[styles.dock, { paddingBottom: insets.bottom + space.sm }]}>
        <View style={[styles.dockRow, frame]}>
          <Press testID="player-mark-button" disabled={disabled} onPress={() => A.edit(q.id, { marked: !cur.marked })} accessibilityLabel={cur.marked ? "Unmark review" : "Mark for review"} accessibilityState={{ selected: !!cur.marked }}
            style={[styles.mark, cur.marked && { backgroundColor: colors.custom_qMarkedSoft }]}>
            <Icon name={cur.marked ? "flag" : "flag-outline"} size={17} color={colors.custom_qMarkedInk} />
            <T w="heavy" size={12.5} numberOfLines={1} color={colors.custom_qMarkedInk}>{cur.marked ? "Marked" : "Mark for review"}</T>
          </Press>
          <Press testID="player-clear-button" disabled={disabled || !has(cur)} onPress={() => A.edit(q.id, { value: "" })} accessibilityLabel="Clear response" style={styles.clear}>
            <T w="bold" size={12.5} color={colors.custom_softText}>Clear</T>
          </Press>
          <Press testID={primary.testID} onPress={primary.onPress} accessibilityLabel={primary.a11y} style={styles.next}>
            <T w="heavy" size={13.5} numberOfLines={1} color={colors.custom_bar}>{primary.label}</T>
            <Icon name="arrow-right" size={17} color={colors.custom_bar} />
          </Press>
        </View>
        <View style={[styles.summary, frame]}>
          <View style={styles.summaryCounts}>
            <Count color={colors.custom_qAnswered} label={`${counts.answered} answered`} testID="player-count-answered" />
            <Count color={colors.custom_qMarked} label={`${counts.marked} marked`} testID="player-count-marked" />
            <Count color={colors.custom_qFreshLine} label={`${questions.length - counts.answered} left`} testID="player-count-left" />
          </View>
          {wide ? null : <Press testID="player-palette-button" onPress={() => setSheet("palette")} accessibilityLabel="Question palette" style={styles.paletteBtn}>
            <Icon name="view-grid" size={14} color={colors.onSurface} />
            <T w="heavy" size={12}>Palette</T>
          </Press>}
        </View>
      </View>
      </View>

      {wide ? (
        <View testID="player-side-panel" style={styles.side}>
          <ScrollView contentContainerStyle={{ padding: space.lg, gap: space.md, paddingBottom: insets.bottom + space.lg }}>
            <T testID="side-palette-label" w="heavy" size={10} color={colors.custom_eyebrow} style={{ letterSpacing: 1.8 }}>QUESTION PALETTE · {nav.subject.toUpperCase()} · {nav.rows.length}</T>
            <Legend counts={subjectCounts} pending={subjectPending} />
            <PaletteGrid prefix="side-q" questions={nav.rows} stateOf={stateOf} currentId={q.id} pendingIds={A.pending} onSelect={qid => { tap(); nav.select(qid); }} />
            {bonusEligible ? <Pill testID="side-bonus-open" kind="outline" label="Enter bonus section" icon="star-plus-outline" onPress={() => setSheet("bonus")} /> : null}
          </ScrollView>
        </View>
      ) : null}
      </View>

      <DSheet visible={sheet === "palette"} onClose={() => setSheet(null)} testID="player-palette-sheet" title="Question palette" closeTestID="palette-close">
        <SubjectSegment prefix="palette-subject" questions={questions} subject={nav.subject} onSelect={nav.selectSubject} answered={answeredOf} />
        <Legend counts={subjectCounts} pending={subjectPending} />
        <T testID="palette-subject-label" w="heavy" size={10} color={colors.custom_eyebrow} style={{ letterSpacing: 1.8 }}>{nav.subject.toUpperCase()} · {nav.rows.length} QUESTIONS</T>
        <PaletteGrid prefix="palette-q" questions={nav.rows} stateOf={stateOf} currentId={q.id} pendingIds={A.pending} onSelect={qid => { nav.select(qid); setSheet(null); }} />
        {bonusEligible ? <Pill testID="player-bonus-open" kind="outline" label="Enter bonus section" icon="star-plus-outline" onPress={() => setSheet("bonus")} /> : null}
        <View style={styles.sheetActions}>
          <Pill testID="palette-back" kind="outline" label="Back to question" onPress={() => setSheet(null)} style={{ flex: 1 }} />
          <Pill testID="player-palette-submit" kind="brand" label="Submit test" onPress={() => setSheet("submit")} style={{ flex: 1 }} />
        </View>
      </DSheet>

      <DSheet visible={sheet === "submit"} onClose={() => setSheet(null)} testID="player-submit-sheet" title="Submit test?">
        <View testID="submit-summary" style={styles.table}>
          <View style={styles.tableRow}>
            <T w="heavy" size={10} color={colors.custom_eyebrow} style={styles.tableName}>SUBJECT</T>
            {["DONE", "MARKED", "LEFT"].map(h => <T key={h} w="heavy" size={10} color={colors.custom_eyebrow} style={styles.tableNum}>{h}</T>)}
          </View>
          {nav.subjects.map(name => {
            const rows = questions.filter((x: any) => subjectOf(x) === name);
            const done = rows.filter(answeredOf).length, marked = rows.filter((x: any) => answer(x)?.marked).length;
            return <View key={name} testID={`submit-subject-${subjectId(name)}`} style={[styles.tableRow, styles.tableLine]}>
              <T w="bold" size={13} style={styles.tableName} numberOfLines={1}>{shortSubject(name)}</T>
              <T w="heavy" size={14} color={colors.custom_qAnswered} style={styles.tableNum}>{done}</T>
              <T w="heavy" size={14} color={colors.custom_qMarkedInk} style={styles.tableNum}>{marked}</T>
              <T w="heavy" size={14} color={colors.custom_qNotAnswered} style={styles.tableNum}>{rows.length - done}</T>
            </View>;
          })}
          <View style={[styles.tableRow, styles.tableLine]}>
            <T w="heavy" size={13} style={styles.tableName}>Total · {questions.length}</T>
            <T testID="submit-total-answered" w="heavy" size={14} style={styles.tableNum}>{counts.answered}</T>
            <T w="heavy" size={14} style={styles.tableNum}>{counts.marked}</T>
            <T w="heavy" size={14} style={styles.tableNum}>{questions.length - counts.answered}</T>
          </View>
        </View>
        {counts.pending ? <Notice tone="warning" testID="submit-pending-warning">Some answers aren’t saved on the server yet. Submit waits until they are — pending answers are never hidden.</Notice> : null}
        <T size={12} color={colors.custom_eyebrow}>Submitting is final. Grading may take a moment; your receipt is kept safely.</T>
        <ErrorBox error={A.error} />
        <Pill testID="player-confirm-submit" kind="brand" size="lg" label="Submit now" busy={busy} onPress={doSubmit} />
        <Pill testID="player-cancel-submit" kind="outline" label="Keep working" onPress={() => setSheet(null)} />
      </DSheet>

      <DSheet visible={sheet === "bonus"} onClose={() => setSheet(null)} testID="player-bonus-sheet" title="Enter the bonus section?">
        <Notice tone="warning">Once you enter, every main-section answer is locked and cannot be edited again.</Notice>
        <Pill testID="player-bonus-confirm" kind="brand" label="Lock main answers & enter bonus" busy={busy} onPress={doBonus} />
        <Pill testID="player-bonus-cancel" kind="outline" label="Not yet" onPress={() => setSheet(null)} />
      </DSheet>

      <DSheet visible={sheet === "exit"} onClose={() => setSheet(null)} testID="player-exit-sheet" title="Leave this attempt?">
        <T size={13} color={colors.muted}>Nothing is submitted. {a.deadline ? "The timer keeps running while you’re away. " : ""}Resume this exact attempt anytime from My Tests.{counts.pending ? " Pending drafts stay on this phone." : ""}</T>
        <Pill testID="player-exit-stay" label="Stay" onPress={() => setSheet(null)} />
        <Pill testID="player-exit-confirm" kind="outline" label="Leave (keep attempt)" onPress={() => router.back()} />
      </DSheet>
    </View>
  );
}

function Count({ color, label, testID }: { color: string; label: string; testID: string }) {
  return <View testID={testID} style={styles.count}>
    <View style={[styles.countDot, { backgroundColor: color }]} />
    <T w="bold" size={11} color={colors.custom_softText} numberOfLines={1}>{label}</T>
  </View>;
}

const styles = StyleSheet.create({
  top: { paddingHorizontal: space.lg, paddingBottom: space.sm, gap: space.md, backgroundColor: colors.surface },
  frame: { width: "100%", maxWidth: COLUMN, alignSelf: "center" },
  body: { flex: 1, flexDirection: "row" },
  side: { width: SIDE, backgroundColor: colors.custom_bar, borderLeftWidth: 1, borderLeftColor: colors.custom_barLine },
  topRow: { flexDirection: "row", alignItems: "center", gap: space.sm },
  saveRow: { flexDirection: "row", alignItems: "center", gap: 5, marginTop: 2 },
  saveDot: { width: 7, height: 7, borderRadius: 4 },
  timer: { flexDirection: "row", alignItems: "center", gap: 5, paddingHorizontal: 12, height: 40, borderRadius: radius.pill, backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLineStrong },
  submitTop: { height: 40, minWidth: 44, paddingHorizontal: 14, borderRadius: radius.pill, backgroundColor: colors.brandPrimary, alignItems: "center", justifyContent: "center" },
  progress: { height: 4, borderRadius: 2, backgroundColor: colors.custom_barLine, overflow: "hidden" },
  qHead: { flexDirection: "row", alignItems: "flex-start", gap: 6 },
  tags: { flexDirection: "row", gap: 6, flexWrap: "wrap" },
  tag: { height: 22, paddingHorizontal: 10, borderRadius: 11, backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLineStrong, justifyContent: "center" },
  question: { backgroundColor: colors.custom_card, borderRadius: 20, borderWidth: 1, borderColor: colors.custom_cardLine, padding: 18, gap: space.md },
  numeric: { height: 64, borderRadius: 16, borderWidth: 1.5, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, paddingHorizontal: space.lg, fontFamily: fonts.heavy, fontSize: 24, color: colors.onSurface },
  option: { flexDirection: "row", alignItems: "center", gap: 14, minHeight: 60, paddingHorizontal: space.lg, paddingVertical: space.md, borderRadius: 16, borderWidth: 1.5, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card },
  optionOn: { borderColor: colors.onSurface, backgroundColor: colors.custom_cardRaised },
  letter: { width: 30, height: 30, borderRadius: 15, borderWidth: 1.5, borderColor: colors.custom_qFreshLine, alignItems: "center", justifyContent: "center" },
  letterOn: { backgroundColor: colors.onSurface, borderColor: colors.onSurface },
  check: { width: 22, height: 22, borderRadius: 11, backgroundColor: colors.onSurface, alignItems: "center", justifyContent: "center" },
  conf: { flexDirection: "row", alignItems: "center", gap: space.sm, flexWrap: "wrap" },
  confChip: { minHeight: 44, paddingHorizontal: 14, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, justifyContent: "center" },
  confOn: { borderColor: colors.custom_mint, backgroundColor: colors.custom_mintSoft },
  dock: { backgroundColor: colors.custom_bar, borderTopWidth: 1, borderTopColor: colors.custom_barLine, paddingHorizontal: space.lg, paddingTop: space.md, gap: space.sm },
  dockRow: { flexDirection: "row", gap: space.sm },
  mark: { flex: 1.15, minWidth: 0, height: 48, borderRadius: radius.pill, borderWidth: 1.5, borderColor: colors.custom_qMarked, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 5, paddingHorizontal: 8 },
  clear: { width: 64, height: 48, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, alignItems: "center", justifyContent: "center" },
  next: { flex: 1.1, minWidth: 0, height: 48, borderRadius: radius.pill, backgroundColor: colors.onSurface, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 5, paddingHorizontal: 8 },
  summary: { flexDirection: "row", alignItems: "center", gap: space.sm },
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
