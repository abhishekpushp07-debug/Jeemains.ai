import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { BackHandler, ScrollView, TextInput, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { useAttempt } from "@/src/useAttempt";
import { availableQuestions, imagePaths, usePaperAssets } from "@/src/assets/paperAssets";
import { SubjectTabs, QuestionGrid, useSubjectNavigation } from "@/src/components/player/SubjectNavigation";
import { AssetProgress } from "@/src/components/player/AssetProgress";
import { invalidate } from "@/src/useCached";
import { AssetImage } from "@/src/components/AssetImage";
import { MathText } from "@/src/components/MathText";
import { Button, Chip, ErrorBox, Icon, IconName, Notice, Press, Sheet, Skeleton, T, tap } from "@/src/components/ui";
import { colors, fonts, foregroundOn, radius, space, subjectColor } from "@/src/theme";
import { fmtClock } from "@/src/navigation";

type QState = "current" | "answered_marked" | "marked" | "answered" | "pending" | "visited" | "fresh";
const QSTYLE: Record<QState, { bg: string; fg: string; icon?: IconName; label: string }> = {
  current: { bg: colors.onSurface, fg: colors.surface, label: "Current" },
  answered_marked: { bg: colors.custom_neonAmber, fg: colors.custom_gameBg, icon: "flag-checkered", label: "Answered & marked" },
  marked: { bg: colors.brandPrimary, fg: colors.onBrandPrimary, icon: "flag", label: "Marked" },
  answered: { bg: colors.success, fg: colors.onSuccess, icon: "check", label: "Answered (saved)" },
  pending: { bg: colors.warning, fg: colors.onWarning, icon: "cloud-upload-outline", label: "Pending save" },
  visited: { bg: colors.borderStrong, fg: colors.onSurface, icon: "eye-outline", label: "Visited" },
  fresh: { bg: colors.border, fg: colors.muted, label: "Not visited" },
};
const CONF = [[0.25, "Guess"], [0.5, "Unsure"], [0.75, "Fairly sure"], [1, "Certain"]] as const;

export default function Player() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { user } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const toResult = () => { invalidate(`u.${user?.id}.`); router.replace(`/result/${id}`); };
  const A = useAttempt(id!, user?.id || "anon", toResult);
  const a = A.attempt;
  const [sheet, setSheet] = useState<null | "palette" | "submit" | "exit" | "bonus">(null);
  const [busy, setBusy] = useState(false);
  const [conf, setConf] = useState<Record<string, number | undefined>>({});
  const reading = useRef<React.ElementRef<typeof ScrollView>>(null);
  const [painted, setPainted] = useState<Record<string, boolean>>({});
  const imageLoaded = useCallback((path: string) => setPainted(old => old[path] ? old : { ...old, [path]: true }), []);
  const imageFailed = useCallback((path: string) => setPainted(old => old[path] === false ? old : { ...old, [path]: false }), []);

  const bonusRule = a?.rules?.bonus_rule;
  const bonusOpen = !!a?.bonus_unlocked_at;
  const questions = useMemo(() => availableQuestions<any>(a?.questions || [], bonusOpen), [a?.questions, bonusOpen]);
  const nav = useSubjectNavigation<any>(questions);
  const q = nav.question;
  const images = usePaperAssets(id!, questions, q?.id, false);
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
      {!A.error ? <><Skeleton h={60} /><Skeleton h={260} /></> : <Button testID="player-back-button" kind="secondary" label="Back" onPress={() => router.back()} />}
    </View>
  );

  const answer = (x: any) => A.pending[x.id] || a.answers?.[x.id];
  const stateOf = (x: any): QState => {
    if (x.id === q?.id) return "current";
    const v = answer(x);
    if (A.pending[x.id]) return "pending";
    const has = !!String(v?.value || "").trim();
    if (has && v?.marked) return "answered_marked";
    if (v?.marked) return "marked";
    if (has) return "answered";
    if (a.visited?.includes(x.id)) return "visited";
    return "fresh";
  };
  const cur = answer(q) || { value: "", marked: false };
  const lockedMain = bonusOpen && !q?.bonus;
  const timeUp = A.seconds === 0;
  const missingImage = q ? imagePaths(id!, q, "question").some(path => !painted[path]) : false;
  const disabled = timeUp || A.conflict || lockedMain || missingImage;
  const saveState = A.conflict ? ["Conflict", colors.error, "alert-octagon-outline"] : !A.online ? ["Offline", colors.error, "wifi-off"] : A.inflight ? ["Saving…", colors.info, "cloud-sync-outline"] : Object.keys(A.pending).length ? [`${Object.keys(A.pending).length} pending`, colors.warning, "cloud-upload-outline"] : ["All saved", colors.success, "cloud-check-outline"];
  const idx = nav.index;
  const go = (d: number) => { const n = nav.rows[idx + d]; if (n) { tap(); nav.select(n.id); } };
  const nextSubject = nav.subjects[nav.subjects.indexOf(nav.subject) + 1];
  const counts = { answered: questions.filter((x: any) => String(answer(x)?.value || "").trim()).length, marked: questions.filter((x: any) => answer(x)?.marked).length, pending: Object.keys(A.pending).length };
  const bonusEligible = bonusRule && !bonusOpen && (a.questions || []).filter((x: any) => !x.bonus).every((x: any) => String(answer(x)?.value || "").trim());

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

  return (
    <View testID="player-screen" style={{ flex: 1, backgroundColor: colors.surface }}>
      <View style={{ paddingTop: insets.top + space.xs, paddingHorizontal: space.md, paddingBottom: space.sm, backgroundColor: colors.surfaceSecondary, borderBottomWidth: 1, borderBottomColor: colors.border, gap: space.sm }}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
          <Press testID="player-exit-button" onPress={() => setSheet("exit")} accessibilityLabel="Leave attempt" style={{ width: 44, height: 44, alignItems: "center", justifyContent: "center" }}>
            <Icon name="close" size={24} color={colors.onSurface} />
          </Press>
          <View style={{ flex: 1 }}>
            <T w="heavy" size={14} numberOfLines={1}>{a.title}</T>
            <View testID="player-save-status" style={{ flexDirection: "row", alignItems: "center", gap: 4 }} accessibilityLiveRegion="polite">
              <Icon name={saveState[2] as IconName} size={13} color={saveState[1]} />
              <T w="bold" size={11} color={saveState[1]}>{saveState[0]}</T>
            </View>
          </View>
          {a.deadline ? (
            <View testID="player-timer" accessibilityLabel={`Time left ${fmtClock(A.seconds ?? 0)}`} style={{ flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 10, height: 36, borderRadius: radius.pill, backgroundColor: (A.seconds ?? 999) < 300 ? colors.custom_errorSoft : colors.surface }}>
              <Icon name="timer-outline" size={16} color={(A.seconds ?? 999) < 300 ? colors.error : colors.onSurface} />
              <T w="heavy" size={15} color={(A.seconds ?? 999) < 300 ? colors.error : colors.onSurface} style={{ fontVariant: ["tabular-nums"] }}>{fmtClock(A.seconds ?? 0)}</T>
            </View>
          ) : <T size={12} w="bold" color={colors.muted}>Untimed</T>}
          <Press testID="player-palette-button" onPress={() => setSheet("palette")} accessibilityLabel="Question palette" style={{ width: 44, height: 44, alignItems: "center", justifyContent: "center" }}>
            <Icon name="view-grid-outline" size={24} color={colors.onSurface} />
          </Press>
        </View>
        <SubjectTabs prefix="player-subject" questions={questions} subject={nav.subject} onSelect={nav.selectSubject} />
        <T testID="player-subject-position" size={11} color={colors.muted}>{nav.subject} · {idx + 1} of {nav.rows.length} · Q{q?.number}</T>
        <AssetProgress prefix="player" progress={images} />
      </View>

      <ScrollView ref={reading} contentContainerStyle={{ padding: space.md, gap: space.md, paddingBottom: space.xl }} keyboardShouldPersistTaps="handled">
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
        {missingImage ? <Notice testID="player-image-wait" tone="info">Loading this question’s original images. You can navigate freely; answering unlocks when they display.</Notice> : null}

        {q ? (
          <View testID="question-reading-surface" style={{ backgroundColor: colors.custom_reading, borderRadius: radius.lg, padding: space.lg, gap: space.md, borderWidth: 1, borderColor: colors.border }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
              <View style={{ paddingHorizontal: 10, height: 28, borderRadius: radius.pill, backgroundColor: subjectColor(q.subject), justifyContent: "center" }}>
                <T w="heavy" size={13} color={foregroundOn(subjectColor(q.subject))}>Q{q.number}</T>
              </View>
              <T size={12} w="bold" color={colors.muted}>{q.type === "integer" ? "Integer answer" : "Single correct"}{q.bonus ? " · Bonus" : ""}</T>
            </View>
            {q.render_mode !== "source" && q.text ? <MathText testID="player-question-text" size={16} text={q.text} /> : null}
            {imagePaths(id!, q, "question").map((path, i) => (
              <AssetImage key={path} testID={`question-image-${q.number}-${i}`} path={path} label={`Question ${q.number} original image`} onLoaded={imageLoaded} onFailed={imageFailed} />
            ))}
            {q.render_mode === "source" && q.text ? <T size={11} color={colors.muted}>{q.text}</T> : null}
          </View>
        ) : null}

        {q?.type === "integer" ? (
          <TextInput testID="player-integer-input" editable={!disabled} value={cur.value} onChangeText={(v) => A.edit(q.id, { value: v.slice(0, 30) })} keyboardType="numbers-and-punctuation" placeholder="Type an exact integer"
            placeholderTextColor={colors.muted} style={{ height: 56, borderRadius: radius.md, borderWidth: 1.5, borderColor: colors.borderStrong, backgroundColor: colors.custom_reading, paddingHorizontal: space.lg, fontFamily: fonts.bold, fontSize: 20, color: colors.custom_onReading }} />
        ) : q ? (
          <View style={{ gap: space.sm }}>
            {Object.entries(q.options || {}).map(([k, label]) => {
              const sel = cur.value === k;
              return (
                <Press key={k} testID={`player-option-${k}`} disabled={disabled} onPress={() => {
                    // Exam mode: the student moves on with Next (lets them review, mark confidence, change answer).
                    A.edit(q.id, { value: sel ? "" : k, ...(conf[q.id] != null ? { confidence: conf[q.id] } : {}) });
                  }} accessibilityLabel={`Option ${k}${sel ? ", selected" : ""}`}
                  style={{ flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 56, paddingHorizontal: space.md, borderRadius: radius.md, borderWidth: 2, borderColor: sel ? colors.brandPrimary : colors.border, backgroundColor: sel ? colors.custom_infoSoft : colors.custom_reading }}>
                  <View style={{ width: 34, height: 34, borderRadius: 17, alignItems: "center", justifyContent: "center", backgroundColor: sel ? colors.brandPrimary : colors.surface }}>
                    <T w="heavy" size={15} color={sel ? colors.onBrandPrimary : colors.onSurface}>{k}</T>
                  </View>
                  <T size={14} w={sel ? "bold" : "medium"} style={{ flex: 1 }} color={colors.custom_onReading}>{String(label).startsWith("See original") ? `Option ${k} (see image)` : String(label)}</T>
                  {sel ? <Icon name="check-circle" size={22} color={colors.brandText} /> : null}
                </Press>
              );
            })}
          </View>
        ) : null}

        {q && !a.confidence_observations?.[q.id] ? (
          <View testID="player-confidence" style={{ gap: 6 }}>
            <T size={11} w="bold" color={colors.muted}>OPTIONAL · HOW SURE ARE YOU?</T>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: space.sm }}>
              {CONF.map(([v, l]) => <Chip key={l} testID={"confidence-" + v} label={l} active={conf[q.id] === v} onPress={() => {
                const nv = conf[q.id] === v ? undefined : v;
                setConf((c) => ({ ...c, [q.id]: nv }));
                // Already answered: save confidence right away with the existing answer.
                if (nv != null && String(cur.value || "").trim()) A.edit(q.id, { value: cur.value, confidence: nv });
              }} />)}
            </ScrollView>
          </View>
        ) : null}
      </ScrollView>

      <View style={{ flexDirection: "row", gap: space.sm, paddingHorizontal: space.md, paddingTop: space.sm, paddingBottom: insets.bottom + space.sm, backgroundColor: colors.surfaceSecondary, borderTopWidth: 1, borderTopColor: colors.border }}>
        <Press testID="player-prev-button" disabled={idx <= 0} onPress={() => go(-1)} accessibilityLabel="Previous question" style={{ width: 48, height: 50, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, alignItems: "center", justifyContent: "center" }}>
          <Icon name="chevron-left" size={26} color={colors.onSurface} />
        </Press>
        <Press testID="player-mark-button" disabled={disabled} onPress={() => A.edit(q.id, { marked: !cur.marked })} accessibilityLabel={cur.marked ? "Unmark review" : "Mark for review"} style={{ flex: 1, height: 50, borderRadius: radius.md, borderWidth: 1, borderColor: cur.marked ? colors.custom_amber : colors.border, backgroundColor: cur.marked ? colors.custom_warningSoft : colors.surfaceSecondary, alignItems: "center", justifyContent: "center", flexDirection: "row", gap: 4 }}>
          <Icon name={cur.marked ? "flag" : "flag-outline"} size={18} color={colors.custom_neonAmber} />
          <T w="bold" size={12}>{cur.marked ? "Marked" : "Mark"}</T>
        </Press>
        <Press testID="player-clear-button" disabled={disabled || !String(cur.value || "").trim()} onPress={() => A.edit(q.id, { value: "" })} accessibilityLabel="Clear response" style={{ flex: 1, height: 50, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, alignItems: "center", justifyContent: "center", flexDirection: "row", gap: 4 }}>
          <Icon name="eraser" size={18} color={colors.muted} />
          <T w="bold" size={12}>Clear</T>
        </Press>
        {idx < nav.rows.length - 1 ? (
          <Press testID="player-next-button" onPress={() => go(1)} style={{ flex: 1.4, height: 50, borderRadius: radius.md, backgroundColor: colors.brandPrimary, alignItems: "center", justifyContent: "center", flexDirection: "row", gap: 4 }}>
            <T w="heavy" size={14} color={colors.onBrandPrimary}>Next</T>
            <Icon name="chevron-right" size={20} color={colors.onBrandPrimary} />
          </Press>
        ) : nextSubject ? (
          <Press testID="player-next-subject" onPress={() => nav.selectSubject(nextSubject)} accessibilityLabel={`Continue to ${nextSubject}`} style={{ flex: 1.4, minHeight: 50, borderRadius: radius.md, backgroundColor: colors.brandPrimary, alignItems: "center", justifyContent: "center" }}>
            <T w="heavy" size={12} color={colors.onBrandPrimary}>Next subject</T>
          </Press>
        ) : (
          <Press testID="player-open-submit" onPress={() => setSheet("submit")} style={{ flex: 1.4, height: 50, borderRadius: radius.md, backgroundColor: colors.surfaceInverse, alignItems: "center", justifyContent: "center" }}>
            <T w="heavy" size={14} color={colors.onSurfaceInverse}>Submit</T>
          </Press>
        )}
      </View>

      <Sheet visible={sheet === "palette"} onClose={() => setSheet(null)} testID="player-palette-sheet">
        <T w="heavy" size={18}>Questions</T>
        <SubjectTabs prefix="palette-subject" questions={questions} subject={nav.subject} onSelect={nav.selectSubject} />
        <T testID="palette-subject-label" size={12} w="bold">{nav.subject} · {nav.rows.length} questions</T>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
          {(Object.keys(QSTYLE) as QState[]).map((k) => (
            <View key={k} style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
              <View style={{ width: 14, height: 14, borderRadius: 4, backgroundColor: QSTYLE[k].bg, borderWidth: 1, borderColor: colors.borderStrong }} />
              <T size={10} color={colors.muted}>{QSTYLE[k].label}</T>
            </View>
          ))}
        </View>
        <QuestionGrid prefix="palette-q" questions={nav.rows} appearance={item => QSTYLE[stateOf(item)]} onSelect={qid => { nav.select(qid); setSheet(null); }} />
        {bonusEligible ? <Button testID="player-bonus-open" kind="secondary" label="Enter bonus section" icon="star-plus-outline" onPress={() => setSheet("bonus")} /> : null}
        <Button testID="player-palette-submit" label="Review & submit" color={colors.surfaceInverse} onPress={() => setSheet("submit")} />
      </Sheet>

      <Sheet visible={sheet === "submit"} onClose={() => setSheet(null)} testID="player-submit-sheet">
        <T w="heavy" size={20}>Submit this attempt?</T>
        <View style={{ flexDirection: "row", gap: space.sm }}>
          {[["Answered", counts.answered, colors.success], ["Marked", counts.marked, colors.custom_amber], ["Pending save", counts.pending, colors.warning], ["Total", questions.length, colors.onSurface]].map(([l, v, c]) => (
            <View key={String(l)} style={{ flex: 1, padding: space.sm, borderRadius: radius.md, backgroundColor: colors.surface }}>
              <T w="heavy" size={20} color={c as string}>{String(v)}</T>
              <T size={10} color={colors.muted}>{String(l)}</T>
            </View>
          ))}
        </View>
        {counts.pending ? <Notice tone="warning" testID="submit-pending-warning">Some answers aren’t saved on the server yet. Submit waits until they are — pending answers are never hidden.</Notice> : null}
        <T size={12} color={colors.muted}>Submitting is final. Grading may take a moment; your receipt is kept safely.</T>
        <ErrorBox error={A.error} />
        <Button testID="player-confirm-submit" label="Submit now" busy={busy} color={colors.surfaceInverse} onPress={doSubmit} />
        <Button testID="player-cancel-submit" kind="secondary" label="Keep working" onPress={() => setSheet(null)} />
      </Sheet>

      <Sheet visible={sheet === "bonus"} onClose={() => setSheet(null)} testID="player-bonus-sheet">
        <T w="heavy" size={19}>Enter the bonus section?</T>
        <Notice tone="warning">Once you enter, every main-section answer is locked and cannot be edited again.</Notice>
        <Button testID="player-bonus-confirm" label="Lock main answers & enter bonus" busy={busy} onPress={doBonus} />
        <Button testID="player-bonus-cancel" kind="secondary" label="Not yet" onPress={() => setSheet(null)} />
      </Sheet>

      <Sheet visible={sheet === "exit"} onClose={() => setSheet(null)} testID="player-exit-sheet">
        <T w="heavy" size={19}>Leave this attempt?</T>
        <T size={13} color={colors.muted}>Nothing is submitted. {a.deadline ? "The timer keeps running while you’re away. " : ""}Resume this exact attempt anytime from My Tests.{counts.pending ? " Pending drafts stay on this phone." : ""}</T>
        <Button testID="player-exit-confirm" kind="secondary" label="Leave (keep attempt)" onPress={() => router.back()} />
        <Button testID="player-exit-stay" label="Stay" onPress={() => setSheet(null)} />
      </Sheet>
    </View>
  );
}
