import React, { useCallback, useEffect, useRef, useState } from "react";
import { ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { setStatusBarStyle } from "expo-status-bar";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { ErrorBox, Press, T } from "@/src/components/ui";
import { PaletteContext, rankColors as colors, space } from "@/src/theme";
import { usesNativeTabs } from "@/src/navigation";
import { storage } from "@/src/utils/storage";
import { CollegeReq, FormBody, getMeta, Handover, Meta, predict, PredictOut, Seat, Segment } from "@/src/rank/api";
import { CATEGORY_LABEL, LEVEL, SERIF } from "@/src/rank/tones";
import { branchLabel, DEFAULT_FORM, FormState, InputCard, toBody } from "@/src/rank/InputCard";
import { ResultCard } from "@/src/rank/ResultCard";
import { SeatList } from "@/src/rank/SeatList";
import { CollegeSheet } from "@/src/rank/CollegeSheet";
import { PercentileChart } from "@/src/rank/PercentileChart";
import { Picker, RuleTitle, Switch } from "@/src/rank/controls";
import { BitsatPanel } from "@/src/rank/Bitsat";
import { ComedkPanel } from "@/src/rank/Comedk";
import { ToolGrid, Tool } from "@/src/rank/ToolGrid";
import { RankPredictor } from "@/src/rank/RankPredictor";
import { PercentileRank } from "@/src/rank/PercentileRank";
import { TargetMarks } from "@/src/rank/TargetMarks";
import { Compare } from "@/src/rank/Compare";
import { ShortlistSheet } from "@/src/rank/ShortlistSheet";
import { PdfButton } from "@/src/rank/PdfButton";
import { shareJee } from "@/src/rank/share";
import { shareCard } from "@/src/shareCard";
import { useShareLink } from "@/src/mission/stats";
import { DreamPanel } from "@/src/dream/DreamPanel";
import { setJeeProfile } from "@/src/dream/need";
import { useDreams } from "@/src/dream/store";
import { useShortlist } from "@/src/rank/shortlist";
import { useCompareColleges } from "@/src/rank/colleges";
import { ACCENTS, AccentContext } from "@/src/rank/accent";

const SAVED = "rank.form.v1";
type Exam = "jee" | "bitsat" | "comedk";

function summaryOf(b: FormBody) {
  return [b.percentile !== undefined ? `${b.percentile} percentile` : `${b.marks} marks`, b.percentile === undefined ? LEVEL[b.level].label : null,
    CATEGORY_LABEL[b.category], b.female ? "Female" : null, b.pwd ? "PwD" : null, b.state].filter(Boolean).join(" · ");
}

// JEELIVE.AI Rank: one text-only screen on pure black. The tool tiles are coloured metal cards; everything below stays quiet black. All cut-off data stays on our server.
export default function RankTab() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [tool, setTool] = useState<Tool>("rank");
  // A tool mounts the first time it is opened and then only hides, so its answer is still there when the student comes back.
  const [seen, setSeen] = useState<Tool[]>(["rank"]);
  const openTool = (t: Tool) => { setTool(t); setSeen(s => (s.includes(t) ? s : [...s, t])); };
  // The College predictor's three exams follow the same rule: switching JEE / BITSAT / COMEDK keeps each one's score and list.
  const [exam, setExamNow] = useState<Exam>("jee");
  const [seenExam, setSeenExam] = useState<Exam[]>(["jee"]);
  const setExam = (e: Exam) => { setExamNow(e); setSeenExam(s => (s.includes(e) ? s : [...s, e])); };
  const [comedkSeed, setComedkSeed] = useState<{ marks: number; at: number } | null>(null);
  const [mode, setMode] = useState<"marks" | "chart">("marks");
  const [meta, setMeta] = useState<Meta | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);
  const [open, setOpen] = useState(true);
  const [query, setQuery] = useState<FormBody | null>(null);
  const [segment, setSegment] = useState<Segment>("all");
  const [page, setPage] = useState(1);
  const [res, setRes] = useState<PredictOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<CollegeReq | null>(null);
  const [branchPicker, setBranchPicker] = useState(false);
  const [shortOpen, setShortOpen] = useState(false);
  const saved = useShortlist();
  const colleges = useCompareColleges();
  const dreams = useDreams();
  const ticket = useRef(0);
  const scroll = useRef<React.ComponentRef<typeof ScrollView>>(null);
  const jeeCard = useRef<React.ComponentRef<typeof View>>(null); // the JEE Rank Card: shared as a photo, and with the PDF
  const link = useShareLink();
  // Where the tool's form starts (just under the tiles) and how far the page is scrolled, so a tile tap can bring its form into view.
  const formTop = useRef(0);
  const scrollY = useRef(0);
  const winH = useWindowDimensions().height;
  const tapTool = (t: Tool) => {
    openTool(t);
    if (formTop.current - scrollY.current > winH * 0.62) scroll.current?.scrollTo({ y: Math.max(0, formTop.current - winH * 0.3), animated: true });
  };
  useFocusEffect(useCallback(() => { setStatusBarStyle("light"); return () => setStatusBarStyle("dark"); }, []));
  // Home's Dream card links here: "college" opens the College predictor, "dream" opens the Dream college tool.
  const params = useLocalSearchParams<{ tool?: string; at?: string }>();
  useEffect(() => {
    if (params.tool === "college" || params.tool === "dream") { openTool(params.tool); scroll.current?.scrollTo({ y: 0, animated: false }); }
  }, [params.tool, params.at]);
  // JEE dream colleges get their marks for the category, gender, PwD and state in the College predictor form.
  useEffect(() => { setJeeProfile({ category: form.category, female: form.female, pwd: form.pwd, state: form.state }); }, [form.category, form.female, form.pwd, form.state]);

  const loadMeta = useCallback(() => {
    setMetaError(null);
    getMeta().then(setMeta).catch(e => setMetaError(e.message));
  }, []);
  useEffect(() => {
    loadMeta();
    storage.getItem<string | null>(SAVED, null).then(raw => {
      if (!raw) return;
      try { setForm({ ...DEFAULT_FORM, ...JSON.parse(raw) }); } catch { /* keep defaults */ }
    });
  }, [loadMeta]);

  const run = useCallback((q: FormBody, seg: Segment, pg: number) => {
    const mine = ++ticket.current;
    setBusy(true); setError(null);
    predict({ ...q, segment: seg, page: pg })
      .then(d => { if (mine === ticket.current) setRes(d); })
      .catch(e => { if (mine === ticket.current) setError(e.message); })
      .finally(() => { if (mine === ticket.current) setBusy(false); });
  }, []);
  useEffect(() => { if (query) run(query, segment, page); }, [query, segment, page, run]);

  const patch = (p: Partial<FormState>) => setForm(f => ({ ...f, ...p }));
  const show = (body: FormBody) => {
    storage.setItem(SAVED, JSON.stringify(form));
    setPage(1); setQuery(body); setOpen(false);
    scroll.current?.scrollTo({ y: 0, animated: false });
  };
  const setBranches = (branches: string[]) => {
    patch({ branches });
    setQuery(q => (q ? { ...q, branches } : q));
    setPage(1);
  };
  const openSeat = (s: Seat, body: FormBody | null = query) => {
    if (body) setDetail({ ...body, inst: s.inst, prog: s.prog, quota: s.quota, gender: s.gender, seat: s.seat });
  };
  // Any Rank tool -> College predictor with the same score already filled in and shown.
  const goColleges = (q: Handover) => {
    if (q.exam === "jee") {
      const nf: FormState = { ...form, marks: q.marks !== undefined ? String(q.marks) : "", pct: q.percentile !== undefined ? String(q.percentile) : "",
        level: q.level ?? form.level, category: q.category ?? form.category, pwd: q.pwd ?? form.pwd };
      const body = toBody(nf);
      setForm(nf); setExam("jee"); setMode("marks");
      if (typeof body !== "string") { storage.setItem(SAVED, JSON.stringify(nf)); setSegment("all"); setPage(1); setQuery(body); setOpen(false); }
    } else if (q.marks !== undefined) {
      setComedkSeed({ marks: q.marks, at: Date.now() }); setExam("comedk");
    }
    openTool("college");
    scroll.current?.scrollTo({ y: 0, animated: false });
  };
  // Each tool pane carries its form colour (yellow, teal, lime, blood red, sky blue) for the form, chips, fields and buttons inside.
  const pane = (t: Tool, node: React.ReactNode) => seen.includes(t) ? <View key={t} style={[styles.tool, tool !== t && styles.hidden]}>
    <AccentContext.Provider value={ACCENTS[t]}>{node}</AccentContext.Provider>
  </View> : null;
  const examPane = (e: Exam, node: React.ReactNode) => seenExam.includes(e) ? <View key={e} style={[styles.tool, exam !== e && styles.hidden]}>{node}</View> : null;

  return (
    <PaletteContext.Provider value={colors}>
    <View style={{ flex: 1, backgroundColor: colors.custom_rankBg }}>
      <ScrollView ref={scroll} testID="rank-screen" keyboardShouldPersistTaps="handled" indicatorStyle="white"
        onScroll={e => { scrollY.current = e.nativeEvent.contentOffset.y; }} scrollEventThrottle={64}
        contentContainerStyle={{ paddingTop: insets.top + space.lg, paddingBottom: (usesNativeTabs ? insets.bottom : 0) + space.xxl, paddingHorizontal: space.lg, gap: space.lg }}>
        <View style={{ gap: 6 }}>
          <RuleTitle>JEELIVE.AI · Rank</RuleTitle>
          <T testID="rank-title" style={styles.title}>Rank & college predictor</T>
          <T size={12.5} color={colors.muted}>JoSAA · CSAB · JAC Delhi · BITSAT · COMEDK, 2026 cutoffs</T>
        </View>
        <View onLayout={e => { formTop.current = e.nativeEvent.layout.y + e.nativeEvent.layout.height + space.lg; }}>
          <ToolGrid value={tool} onChange={tapTool} saved={saved.length} colleges={colleges.length} dreams={dreams.dreams.length} />
        </View>

        {pane("rank", <RankPredictor onColleges={goColleges} />)}
        {pane("pct", <PercentileRank onColleges={goColleges} />)}
        {pane("target", <TargetMarks states={meta?.states ?? []} />)}
        {pane("compare", <Compare onGoCollege={() => openTool("college")}
          profile={{ category: form.category, female: form.female, pwd: form.pwd, state: form.state }} />)}
        {pane("dream", <DreamPanel onAdd={() => tapTool("college")} />)}
        {pane("college", <>
        <Switch prefix="rank-exam" value={exam} onChange={setExam} items={[{ key: "jee", label: "JEE Main" }, { key: "bitsat", label: "BITSAT" }, { key: "comedk", label: "COMEDK" }]} />

        {examPane("bitsat", <BitsatPanel onShortlist={() => setShortOpen(true)} />)}
        {examPane("comedk", <>
            <ErrorBox error={metaError ?? undefined} retry={loadMeta} testID="comedk-meta-error" />
            <ComedkPanel groups={meta?.comedk.groups ?? []} seed={comedkSeed} onSeedUsed={() => setComedkSeed(null)} onShortlist={() => setShortOpen(true)} />
          </>)}
        {examPane("jee", <>
          <Switch prefix="rank-mode" value={mode} onChange={setMode} items={[{ key: "marks", label: "My marks" }, { key: "chart", label: "Percentile chart" }]} />
          <ErrorBox error={metaError ?? undefined} retry={loadMeta} testID="rank-meta-error" />

          {mode === "marks" ? <>
            <InputCard form={form} onChange={patch} states={meta?.states ?? []} branches={meta?.branches ?? []} open={open}
              summary={query ? summaryOf(query) : ""} onShow={show} onEdit={() => setOpen(true)} busy={busy && !res} />
            <ErrorBox error={error ?? undefined} retry={() => query && run(query, segment, page)} testID="rank-error" />
            {res && query ? <>
              <ResultCard result={res.result} candidates={meta?.candidates} saved={saved.length} onShortlist={() => setShortOpen(true)}
                cardRef={jeeCard} onShare={() => shareCard(jeeCard, shareJee(res.result, res.items, link))} />
              <SeatList data={res} segment={segment} onSegment={s => { setSegment(s); setPage(1); }} page={page} onPage={setPage}
                branchText={branchLabel(form.branches)} onBranch={() => setBranchPicker(true)} onOpen={s => openSeat(s)} busy={busy}
                tools={<PdfButton testID="rank-pdf" path="/jee" body={{ ...query, segment }} label="Top 50 ki PDF" card={jeeCard} />} />
            </> : null}
          </> : meta ? <PercentileChart lines={meta.chart} branches={form.branches} branchText={branchLabel(form.branches)}
            onBranch={() => setBranchPicker(true)} onOpen={(s, body) => openSeat(s, body)} /> : null}

          <View style={{ gap: 4 }}>
            <T size={12} color={colors.muted}>{meta?.note ?? "2026 ke data par estimate. Asli cutoff har saal badalta hai."}</T>
            <T size={11.5} color={colors.custom_dim}>Data: NTA JEE Main 2026, JoSAA 2026 Round 1–5, CSAB Special 2026 Round 1–2, JAC Delhi 2026 Round 1–4. Trend: JoSAA 2025 final round.</T>
            {meta?.missing.map(m => <T key={m} size={11.5} color={colors.custom_dim}>{m}</T>)}
          </View>
        </>)}
        </>)}

        <View style={styles.links}>
          <Press testID="rank-open-series" onPress={() => router.push("/live")} style={styles.link} accessibilityLabel="All India series">
            <T w="bold" size={13.5} color={colors.brandText}>All India series</T>
          </Press>
          <Press testID="rank-open-results" onPress={() => router.push({ pathname: "/(tabs)/tests", params: { tab: "completed", at: String(Date.now()) } })} style={styles.link} accessibilityLabel="My results">
            <T w="bold" size={13.5} color={colors.brandText}>My results</T>
          </Press>
        </View>
      </ScrollView>
      <Picker visible={branchPicker} title="Branch" options={meta?.branches ?? []} value={form.branches} multi allLabel="All branches"
        onChange={setBranches} onClose={() => setBranchPicker(false)} testID="rank-list-branch-picker" />
      <ShortlistSheet visible={shortOpen} onClose={() => setShortOpen(false)} onOpen={query ? s => openSeat(s) : undefined} />
      {detail ? <CollegeSheet key={`${detail.inst}-${detail.prog}-${detail.percentile}-${detail.marks}`} req={detail} onClose={() => setDetail(null)} /> : null}
    </View>
    </PaletteContext.Provider>
  );
}

const styles = StyleSheet.create({
  title: { fontFamily: SERIF, fontSize: 31, lineHeight: 38, color: colors.onSurface, textShadowColor: colors.custom_rankChrome, textShadowOffset: { width: 0, height: 0 }, textShadowRadius: 12 },
  links: { flexDirection: "row", gap: space.xl, justifyContent: "center" },
  tool: { gap: space.lg },
  hidden: { display: "none" },
  link: { minHeight: 44, justifyContent: "center" },
});
