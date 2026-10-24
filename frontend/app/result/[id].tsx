import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { FlatList, ScrollView, TextInput, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { api, apiRaw, post, put, uuid } from "@/src/api/client";
import { AssetImage } from "@/src/components/AssetImage";
import { AiSolution } from "@/src/components/AiSolution";
import { useCached } from "@/src/useCached";
import { Button, Card, Chip, Empty, ErrorBox, Header, Icon, IconName, Notice, Press, Sheet, Skeleton, Stat, T } from "@/src/components/ui";
import { colors, fonts, radius, space, subjectColor } from "@/src/theme";
import { fmtClock, unixDate } from "@/src/navigation";

type Tab = "analysis" | "progress" | "confidence" | "rank" | "solutions";
const TABS: [Tab, string, IconName][] = [["analysis", "Analysis", "chart-donut"], ["progress", "Progress", "chart-line"], ["confidence", "Confidence", "gauge"], ["rank", "Rank", "podium"], ["solutions", "Solutions", "book-open-variant"]];
const FILTERS = [["all", "All"], ["incorrect", "Incorrect"], ["correct", "Correct"], ["skipped", "Skipped"], ["marked", "Marked"]] as const;
const OUT: Record<string, [string, IconName]> = { correct: [colors.success, "check"], incorrect: [colors.error, "close"], skipped: [colors.muted, "minus"], dropped: [colors.muted, "cancel"], bonus: [colors.custom_amber, "star"] };
const CATS = [["concept_gap", "Concept gap"], ["calculation", "Calculation"], ["silly_mistake", "Silly mistake"], ["time_pressure", "Time pressure"], ["misread", "Misread"], ["guess", "Guess"], ["other", "Other"]];
const matches = (q: any, f: string) => f === "all" || (f === "marked" ? q.marked : q.outcome === f);
const view = { tab: "analysis" as Tab, filter: "all", subject: "", qid: "" };

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

function Analysis({ r }: { r: any }) {
  const s = r.summary;
  return (
    <View style={{ gap: space.md }}>
      <Card testID="result-score-card" style={{ gap: space.md, backgroundColor: colors.surfaceInverse, borderColor: colors.surfaceInverse }}>
        <T w="bold" size={11} color={colors.custom_whiteA70} style={{ letterSpacing: 1 }}>YOUR SCORE · {r.score_version === "original" ? "ORIGINAL" : "REVISED"}</T>
        <T w="heavy" size={40} color={colors.onSurfaceInverse} testID="result-score">{s.score}<T w="semibold" size={20} color={colors.custom_whiteA70}> / {s.maximum}</T></T>
        <T size={12} color={colors.custom_whiteA70}>{r.rules ? `+${r.rules.correct} / ${r.rules.wrong} / 0 marking` : ""}{s.total_seconds ? ` · ${fmtClock(s.total_seconds)} used` : ""}</T>
      </Card>
      <View style={{ flexDirection: "row", gap: space.sm }}>
        <Stat testID="result-correct" label="Correct" value={s.correct} color={colors.success} />
        <Stat testID="result-incorrect" label="Incorrect" value={s.incorrect} color={colors.error} />
        <Stat testID="result-skipped" label="Skipped" value={s.skipped} />
      </View>
      <View style={{ flexDirection: "row", gap: space.sm }}>
        <Stat label="Accuracy" value={s.accuracy != null ? s.accuracy + "%" : "—"} />
        <Stat label="Attempt rate" value={s.attempt_rate != null ? s.attempt_rate + "%" : "—"} />
        <Stat label="Penalty" value={s.penalties ?? 0} color={colors.error} />
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
            <View style={{ height: 8, borderRadius: 4, backgroundColor: colors.border, overflow: "hidden" }}>
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
  const [d, setD] = useState<any>(null);
  const [e, setE] = useState("");
  const [n, setN] = useState(0);
  useEffect(() => { setD(null); setE(""); api(path).then(setD).catch((x) => setE(x.message)); }, [path, n]);
  if (e) return <ErrorBox error={e} retry={() => setN((x) => x + 1)} />;
  if (!d) return <Skeleton h={140} />;
  return <>{render(d)}</>;
}

function Unavailable({ title, reason, testID }: { title: string; reason?: string; testID: string }) {
  return <Card testID={testID}><Empty icon="information-outline" title={title} body={reason} /></Card>;
}

function Solutions({ r, id, version }: { r: any; id: string; version: string }) {
  const rows: any[] = useMemo(() => r.questions || [], [r.questions]);
  const subjects = useMemo(() => [...new Set(rows.map((q) => q.subject || "General"))] as string[], [rows]);
  const [filter, setFilter] = useState(view.filter);
  const initial = rows.find((q) => q.id === view.qid);
  const [subject, setSubject] = useState(initial?.subject || (subjects.includes(view.subject) ? view.subject : subjects[0]));
  const list = rows.filter((q) => (q.subject || "General") === subject && matches(q, filter));
  const [qid, setQid] = useState(initial?.id || list[0]?.id || "");
  const q = rows.find((x) => x.id === qid && (x.subject || "General") === subject && matches(x, filter)) || list[0];
  Object.assign(view, { filter, subject, qid: q?.id || "" });
  const rail = useRef<FlatList>(null);
  const [opened, setOpened] = useState<Record<string, "ok" | "err">>({});
  const [report, setReport] = useState(false);
  // AI step-by-step solutions generated on the JEELIVE backend (more arrive over time; refetched on open).
  const ai = useCached<any>(`ai.${id}`, (signal) => api(`/attempts/${id}/ai-solutions`, { signal }), false);
  const aiBy = useMemo(() => Object.fromEntries((ai.data?.items || []).map((x: any) => [x.question_id, x])), [ai.data]);

  useEffect(() => {
    const i = list.findIndex((x) => x.id === q?.id);
    if (i >= 0) setTimeout(() => rail.current?.scrollToIndex({ index: i, viewPosition: 0.5, animated: false }), 50);
  }, [q?.id, subject, filter]); // eslint-disable-line react-hooks/exhaustive-deps
  const consult = useCallback(async (x: any) => {
    try { await post(`/attempts/${id}/questions/${x.id}/solution-open`, {}); setOpened((o) => ({ ...o, [x.id]: "ok" })); } catch { setOpened((o) => ({ ...o, [x.id]: "err" })); }
  }, [id]);
  useEffect(() => { if (q && !opened[q.id]) consult(q); }, [q?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <View style={{ gap: space.md }} testID="solution-navigator">
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: space.sm }}>
        {FILTERS.map(([v, l]) => <Chip key={v} testID={"solution-filter-" + v} label={l} active={filter === v} count={rows.filter((x) => matches(x, v)).length} onPress={() => setFilter(v)} color={colors.surfaceInverse} />)}
      </ScrollView>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 6 }}>
        {subjects.map((s) => (
          <Press key={s} testID={"solution-subject-" + s.toLowerCase().replace(/\s+/g, "-")} onPress={() => { setSubject(s); setQid(""); }} style={{ height: 34, paddingHorizontal: 12, borderRadius: radius.sm, justifyContent: "center", backgroundColor: subject === s ? subjectColor(s) : colors.surfaceSecondary, borderWidth: 1, borderColor: subject === s ? subjectColor(s) : colors.border }}>
            <T w="heavy" size={12} color={subject === s ? colors.onBrandPrimary : colors.onSurface}>{s} · {rows.filter((x) => (x.subject || "General") === s && matches(x, filter)).length}</T>
          </Press>
        ))}
      </ScrollView>
      {list.length ? (
        <FlatList ref={rail} testID="solution-question-rail" horizontal showsHorizontalScrollIndicator={false} data={list} keyExtractor={(x) => x.id} contentContainerStyle={{ gap: 8, paddingRight: space.xl }}
          getItemLayout={(_, i) => ({ length: 52, offset: 52 * i, index: i })} onScrollToIndexFailed={() => {}}
          renderItem={({ item }) => {
            const [c, ic] = OUT[item.outcome] || OUT.skipped;
            const sel = item.id === q?.id;
            return (
              <Press testID={"solution-question-" + item.number} onPress={() => setQid(item.id)} accessibilityLabel={`Question ${item.number}, ${item.outcome}${item.marked ? ", marked" : ""}${sel ? ", selected" : ""}`}
                style={{ width: 44, height: 48, borderRadius: 10, alignItems: "center", justifyContent: "center", backgroundColor: sel ? colors.surfaceInverse : colors.surfaceSecondary, borderWidth: 2, borderColor: sel ? colors.surfaceInverse : c }}>
                <T w="heavy" size={14} color={sel ? colors.onSurfaceInverse : colors.onSurface}>{item.number}</T>
                <Icon name={item.marked ? "flag" : ic} size={11} color={sel ? colors.onSurfaceInverse : c} />
              </Press>
            );
          }} />
      ) : (
        <Card testID="solution-empty-filter"><Empty icon="filter-off-outline" title={`No ${filter} questions in ${subject}.`} action={<Button testID="solution-show-all" kind="secondary" label="Show all questions" onPress={() => setFilter("all")} />} /></Card>
      )}
      {q ? (
        <View testID="solution-card" style={{ backgroundColor: colors.custom_reading, borderRadius: radius.lg, padding: space.lg, gap: space.md, borderWidth: 1, borderColor: colors.border }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
            <T w="heavy" size={16}>Q{q.number}</T>
            <View style={{ paddingHorizontal: 8, paddingVertical: 2, borderRadius: radius.pill, backgroundColor: (OUT[q.outcome] || OUT.skipped)[0] }}>
              <T w="heavy" size={11} color={colors.onBrandPrimary}>{q.outcome.toUpperCase()} · {q.marks > 0 ? "+" : ""}{q.marks}</T>
            </View>
            {q.marked ? <Icon name="flag" size={16} color={colors.custom_amber} /> : null}
          </View>
          {q.render_mode !== "source" && q.text ? <T size={15} color={colors.custom_onReading}>{q.text}</T> : null}
          {Array.from({ length: q.asset_count || 0 }, (_, i) => <AssetImage key={q.id + "q" + i} testID={`solution-qimage-${q.number}-${i}`} path={`/attempts/${id}/questions/${q.id}/asset/question/${i}`} label={`Question ${q.number}`} />)}
          <View style={{ flexDirection: "row", gap: space.sm }}>
            <View style={{ flex: 1, padding: space.md, borderRadius: radius.md, backgroundColor: colors.surface }}><T size={11} color={colors.muted}>Your answer</T><T w="heavy" size={16} testID="solution-your-answer">{q.response || "—"}</T></View>
            <View style={{ flex: 1, padding: space.md, borderRadius: radius.md, backgroundColor: colors.custom_successSoft }}><T size={11} color={colors.success}>Answer key</T><T w="heavy" size={16} color={colors.success} testID="solution-answer-key">{(q.accepted_answers || [q.answer]).join(" / ")}</T></View>
          </View>
          <T w="bold" size={11} color={colors.muted} style={{ letterSpacing: 1 }}>{q.solution_kind === "answer_key_only" ? "SUPPLIED ANSWER KEY" : "SUPPLIED SOLUTION"}</T>
          {q.solution_kind === "answer_key_only" ? (
            <T size={13} color={colors.custom_onReading} testID={"no-worked-solution-" + q.number}>{aiBy[q.id]?.state === "ready" ? "The source provides this key only. An AI generated step-by-step solution is shown below." : ai.error && !ai.data ? "The source provides this key only." : "The source provides this key only. No worked solution was supplied."}</T>
          ) : q.solution ? <T size={14} color={colors.custom_onReading} testID="solution-text">{q.solution}</T> : null}
          {Array.from({ length: q.solution_asset_count || 0 }, (_, i) => <AssetImage key={q.id + "s" + i} testID={`solution-simage-${q.number}-${i}`} path={`/attempts/${id}/questions/${q.id}/asset/solution/${i}`} label={`Solution ${q.number}`} />)}
          {ai.loading && !ai.data ? <Skeleton h={120} /> : ai.error && !ai.data ? (
            <Press testID="ai-solution-error" onPress={ai.reload} style={{ minHeight: 44, justifyContent: "center" }}><T size={12} w="bold" color={colors.brandPrimary}>Couldn’t load AI solutions. Tap to retry</T></Press>
          ) : <AiSolution item={aiBy[q.id]} number={q.number} disclosure={ai.data?.disclosure} />}
          {opened[q.id] === "err" ? <Press testID="solution-consult-retry" onPress={() => consult(q)}><T size={12} w="bold" color={colors.brandPrimary}>Couldn’t record that you viewed this solution. Retry</T></Press> : null}
          <Reflection id={id} q={q} version={version} state={r.review?.states?.[q.id] || r.review_states?.[q.id]} consulted={opened[q.id] === "ok"} />
          <Button testID="solution-report-button" kind="ghost" icon="flag-outline" label="Report a problem with this question" onPress={() => setReport(true)} color={colors.muted} />
        </View>
      ) : null}
      <ReportSheet visible={report} onClose={() => setReport(false)} id={id} q={q} />
    </View>
  );
}

function Reflection({ id, q, version, state, consulted }: { id: string; q: any; version: string; state?: any; consulted: boolean }) {
  const [s, setS] = useState<any>(state || { revision: 0, category: null, note: "", identified_error: false, wrote_note: false, reviewed_solution: false, retry_planned: false });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => setS(state || { revision: 0, category: null, note: "", identified_error: false, wrote_note: false, reviewed_solution: false, retry_planned: false }), [q.id]); // eslint-disable-line react-hooks/exhaustive-deps
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
    <View testID="reflection-panel" style={{ gap: space.sm, padding: space.md, borderRadius: radius.md, backgroundColor: colors.surface }}>
      <T w="heavy" size={14}>Your reflection {s.completed ? "· steps recorded" : ""}</T>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 6 }}>
        {CATS.map(([v, l]) => <Chip key={v} testID={"reflection-cat-" + v} label={l} active={s.category === v} onPress={() => setS({ ...s, category: s.category === v ? null : v })} />)}
      </ScrollView>
      <TextInput testID="reflection-note-input" value={s.note || ""} onChangeText={(t) => setS({ ...s, note: t.slice(0, 500) })} placeholder="Short private note (max 500)" placeholderTextColor={colors.muted} multiline
        style={{ minHeight: 60, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, padding: space.md, fontFamily: fonts.regular, fontSize: 14, color: colors.onSurface, backgroundColor: colors.surfaceSecondary, textAlignVertical: "top" }} />
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
  useEffect(() => { if (visible) { setReceipt(null); setErr(""); setNote(""); } }, [visible]);
  async function send() {
    try { setReceipt(await post(`/attempts/${id}/questions/${q.id}/report-wrong`, { category: cat, context: "solutions", note: note.slice(0, 600) })); } catch (e: any) { setErr(e.message); }
  }
  return (
    <Sheet visible={visible} onClose={onClose} testID="report-sheet">
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
    </Sheet>
  );
}

export default function Result() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [version, setVersion] = useState("original");
  const [r, setR] = useState<any>(null);
  const [status, setStatus] = useState(0);
  const [err, setErr] = useState("");
  const [tab, setTab] = useState<Tab>(view.tab);
  const [n, setN] = useState(0);
  const polls = useRef(0);
  view.tab = tab;
  const reload = useCallback(() => { polls.current = 0; setN((x) => x + 1); }, []);

  useEffect(() => {
    let alive = true;
    let t: any;
    setErr("");
    apiRaw(`/attempts/${id}/results?score_version=${encodeURIComponent(version)}`).then((res) => {
      if (!alive) return;
      setR(res.data);
      setStatus(res.status);
      if (res.status === 202 && res.data?.grading_status !== "failed" && polls.current < 12) {
        polls.current += 1;
        t = setTimeout(() => setN((x) => x + 1), Math.max(res.retryAfterMs || res.data?.retry_after_ms || 2000, 1500 * polls.current) + Math.random() * 800);
      }
    }).catch((e) => alive && setErr(e.message));
    return () => { alive = false; clearTimeout(t); };
  }, [id, version, n]);

  const ready = status === 200 && r?.summary && r?.status !== "embargoed";
  return (
    <View testID="result-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <Header title={r?.title || "Result"} eyebrow={r?.exam ? `${r.exam} · Result` : "Result"} onBack={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)/tests"))} />
      {ready ? (
        <View style={{ height: 56, justifyContent: "center" }}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: space.sm, paddingHorizontal: space.lg, alignItems: "center" }}>
            {TABS.map(([v, l, ic]) => <Chip key={v} testID={"result-tab-" + v} label={l} icon={ic} active={tab === v} onPress={() => setTab(v)} color={colors.surfaceInverse} />)}
          </ScrollView>
        </View>
      ) : null}
      <ScrollView contentContainerStyle={{ padding: space.lg, paddingTop: space.sm, paddingBottom: insets.bottom + space.xl, gap: space.md }}>
        <ErrorBox error={err} retry={reload} testID="result-error" />
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
        {ready && tab === "analysis" ? <Analysis r={r} /> : null}
        {ready && tab === "progress" ? <Remote path={`/attempts/${id}/journey`} render={(d) => d.state !== "available" ? <Unavailable testID="progress-unavailable" title="Progress journey unavailable" reason={d.reason} /> : (
          <Card testID="progress-journey" style={{ gap: space.sm }}>
            <T w="heavy" size={16}>Your full-mock journey</T>
            {(d.series || []).map((p: any) => <T key={p.id} size={13}>{unixDate(p.submitted_at)} · {p.title}: {p.score}/{p.maximum}</T>)}
          </Card>)} /> : null}
        {ready && tab === "confidence" ? (r.analytics?.confidence ? (
          <Card testID="confidence-card" style={{ gap: space.sm }}>
            <T w="heavy" size={16}>Confidence vs correctness</T>
            {Object.entries(r.analytics.confidence).filter(([, v]) => typeof v !== "object").slice(0, 8).map(([k, v]: any) => <T key={k} size={13}>{k.replace(/_/g, " ")}: {String(v)}</T>)}
          </Card>
        ) : <Unavailable testID="confidence-unavailable" title="No confidence recorded" reason="Confidence is optional. Pick “How sure are you?” before answering next time to see calibration here." />) : null}
        {ready && tab === "rank" ? <Remote path={`/attempts/${id}/historical-rank?score_version=${version}`} render={(d) => d.kind === "branch_matches" ? (
          d.state !== "available" ? <Unavailable testID="rank-unavailable" title="Branch guidance unavailable" reason={d.reason || d.limitation} /> : (
            <Card testID="bitsat-branches" style={{ gap: space.sm }}>
              <T w="heavy" size={16}>Top branch matches</T>
              {d.matches.map((m: any) => <T key={m.programme + m.campus} size={13}>• {m.programme} — {m.campus} (cutoff {m.cutoff}, margin {m.margin})</T>)}
              <T size={11} color={colors.muted}>{d.limitation} Admission is not guaranteed.</T>
            </Card>)
        ) : d.state !== "available" ? <Unavailable testID="rank-unavailable" title={d.label || "Reliable rank estimate unavailable"} reason={d.reason} /> : (
          <Card testID="rank-card" style={{ gap: space.sm }}>
            <T w="bold" size={11} color={colors.muted}>{d.label?.toUpperCase()}</T>
            <T w="heavy" size={26}>{d.rank_low?.toLocaleString("en-IN")} – {d.rank_high?.toLocaleString("en-IN")}</T>
            {d.percentile_low != null ? <T size={13}>Percentile ≈ {d.percentile_low.toFixed(2)} – {d.percentile_high.toFixed(2)}</T> : null}
            <T size={12}>{d.reason}</T>
            <T size={11} color={colors.muted}>{d.limitation}</T>
          </Card>)} /> : null}
        {ready && tab === "solutions" ? <Solutions r={r} id={id!} version={version} /> : null}
      </ScrollView>
    </View>
  );
}
