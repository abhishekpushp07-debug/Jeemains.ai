import React, { useEffect, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, TextInput, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { useAuth } from "@/src/auth";
import { api, del, post } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { useListFocus } from "@/src/useListFocus";
import { Empty, ErrorBox, Icon, Notice, Press, Skeleton, T } from "@/src/components/ui";
import { DSheet, Pill, StatusLine } from "@/src/components/design";
import { GlossTabs, TabLook } from "@/src/components/GlossTabs";
import { RedTabs } from "@/src/components/RedTabs";
import { ScreenMotion } from "@/src/motion";
import { toneInk } from "@/src/components/PyqPaperCard";
import { colors, fonts, noOutline, radius, space, tabEdges } from "@/src/theme";
import { learningStatusTone } from "@/src/components/LearningTheme";
import { EXAMS, fmtClock, unixDate, usesNativeTabs } from "@/src/navigation";
import { useExams } from "@/src/api/examCatalog";
import { timeLabel } from "@/src/choice/api";
import { MockRow, mockOver, useMocks } from "@/src/misfire/mock/store";
import { useSendWaiting } from "@/src/misfire/mock/marking";
import { useSearchTrack } from "@/src/searchTrack";

type Tab = "progress" | "saved" | "completed";
const TABS: Tab[] = ["completed", "progress", "saved"];
// Each tab keeps its own colour (baby pink, yellow, sky blue): full when open, a softer wash when not, with an edge from its own family.
const TAB_LOOK: Record<Tab, TabLook> = {
  completed: { on: [colors.custom_tabPink, colors.custom_tabPinkDeep], rest: [colors.custom_tabPinkSoft, colors.custom_tabPinkSoftDeep], edge: tabEdges.pink, glow: colors.custom_tabPinkGlow },
  progress: { on: [colors.custom_tabSun, colors.custom_tabSunDeep], rest: [colors.custom_tabSunSoft, colors.custom_tabSunSoftDeep], edge: tabEdges.sun, glow: colors.custom_tabSunGlow },
  saved: { on: [colors.custom_tabSky, colors.custom_tabSkyDeep], rest: [colors.custom_tabSkySoft, colors.custom_tabSkySoftDeep], edge: tabEdges.sky, glow: colors.custom_tabSkyGlow },
};
const STATUS_LABEL: Record<string, string> = {
  active: "In progress", expired: "Time expired · finish grading", embargoed: "Result sealed", completed: "Scored", grading: "Preparing result",
};
// Kept at module level so returning to this tab restores the same view.
const memo = { tab: "completed" as Tab, q: "", exam: "" };

/** The website's list keeps its own order; each Misfire Mock (made on this phone) goes in before the first paper older than it. */
const mockTime = (m: MockRow) => Math.round((m.submitted_at || m.started_at || m.made_at) / 1000);
function withMocks(items: any[], mocks: MockRow[]) {
  const left = [...mocks].sort((a, b) => mockTime(b) - mockTime(a)).map(m => ({ ...m, kind: "mock", id: "mock-" + m.id, mock: m }));
  const out: any[] = [];
  for (const it of items) {
    const at = Number(it.submitted_at || it.started_at || 0);
    while (left.length && mockTime(left[0].mock) >= at) out.push(left.shift());
    out.push(it);
  }
  return [...out, ...left];
}

/** A test's card: white, as Home's four exam cards; only the tabs above carry colour. `chosen` = picked for Compare. */
function PaperCard({ testID, chosen, faded, children }: { testID: string; chosen?: boolean; faded?: boolean; children: React.ReactNode }) {
  return <LinearGradient testID={testID} colors={[colors.custom_chipFrom, colors.custom_chipTo]} start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }}
    style={[styles.paper, chosen && styles.paperOn, faded && styles.faded]}>{children}</LinearGradient>;
}

/** A Misfire Mock, on the same white card: made from the student's own Misfire questions and kept on this phone. */
function MockCard({ m, onOpen }: { m: MockRow; onOpen: () => void }) {
  const over = mockOver(m), timeUp = over && m.status !== "done";
  const label = m.status === "done" ? "Scored" : timeUp ? "Time over · result ready" : m.status === "active" ? "In progress" : "Ready to start";
  const left = m.status === "active" && m.deadline && !over ? Math.round((m.deadline - Date.now()) / 1000) : 0;
  const action = over ? "Open result" : m.status === "active" ? "Resume" : "Start";
  return (
    <PaperCard testID={`mock-container-${m.id}`}>
      <Press testID={`mock-card-${m.id}`} onPress={onOpen} scaleTo={0.99} style={styles.attemptContent}>
        <View style={styles.statusRow}>
          <StatusLine testID={`mock-status-${m.id}`} label={label} color={colors.custom_chipBlood} ink={colors.custom_tabInk} />
          <T testID={`mock-exam-${m.id}`} size={11.5} color={colors.custom_tabInkSoft}>Offline Misfire{m.exam && m.exam !== "Mixed" ? ` · ${m.exam}` : ""}</T>
        </View>
        <T testID={`mock-title-${m.id}`} w="heavy" size={17} color={colors.custom_tabInk}>{m.title}</T>
        <T testID={`mock-meta-${m.id}`} size={12} color={colors.custom_tabInkSoft}>
          {m.started_at ? "Started" : "Made"} {unixDate(Math.round((m.started_at || m.made_at) / 1000))} · {m.count} sawaal · {timeLabel(m.minutes)}{left > 0 ? ` · ${fmtClock(left)} left` : ""}
        </T>
        {m.score != null ? <T testID={`mock-score-${m.id}`} w="heavy" size={15} color={m.score < 0 ? colors.custom_chipBloodDeep : colors.custom_tabInk}>{m.score} / {m.maximum} marks{m.accuracy != null ? ` · ${m.accuracy}% accuracy` : ""}</T> : null}
      </Press>
      <View style={styles.actions}>
        <Press testID={`mock-action-${m.id}`} onPress={onOpen} style={[styles.go, over ? styles.goOutline : { backgroundColor: colors.onSurface }]}>
          <T w="heavy" size={12.5} color={over ? colors.custom_tabInk : colors.custom_bar}>{action}</T>
          <Icon name="arrow-right" size={15} color={over ? colors.custom_tabInk : colors.custom_bar} />
        </Press>
      </View>
    </PaperCard>
  );
}

export default function MyTests() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const params = useLocalSearchParams<{ tab?: string; at?: string }>();
  const [tab, setTab] = useState<Tab>(memo.tab);
  const [q, setQ] = useState(memo.q);
  const [query, setQuery] = useState(memo.q);
  const [exam, setExam] = useState(memo.exam);
  const [selected, setSelected] = useState<any[]>([]);
  const [cmp, setCmp] = useState<{ open: boolean; data?: any; error?: string; busy?: boolean }>({ open: false });
  Object.assign(memo, { tab, q: query, exam });
  // Home stat cards open this screen on a chosen tab.
  useEffect(() => {
    if (params.tab && (TABS as string[]).includes(params.tab)) { setTab(params.tab as Tab); setSelected([]); }
  }, [params.tab, params.at]);
  useEffect(() => {
    const t = setTimeout(() => setQuery(q.trim()), 300);
    return () => clearTimeout(t);
  }, [q]);
  const search = new URLSearchParams({ tab, page: "1", q: query, status: "all", exam }).toString();
  const list = useCached<any>(user ? `u.${user.id}.tests.${search}` : null, (signal) => api("/my/tests?" + search, { signal }));
  useSearchTrack("my_tests", query, list.data ? (list.data.items || []).length : null);
  useListFocus(list.revalidate);
  // Exam filters follow the website's exam list, so attempts of a newly added exam can be filtered too.
  const catalog = useExams();
  useListFocus(catalog.revalidate);
  // An exam the owner has hidden cannot stay selected: the website refuses that filter.
  const examKeys = catalog.exams?.map(e => e.key).join("|");
  useEffect(() => { if (exam && examKeys !== undefined && !examKeys.split("|").includes(exam)) setExam(""); }, [exam, examKeys]);
  // The owner's four filters: All exams, JEE Main, BITSAT, COMEDK (an exam the website hides is left out).
  const examTabs = [{ key: "", label: "All exams" }, ...EXAMS.flatMap(e => {
    const live = catalog.exams?.find(x => x.slug === e.slug);
    return live ? [{ key: live.key, label: e.name }] : catalog.exams ? [] : [{ key: e.name, label: e.name }];
  })];
  // Misfire Mocks live on this phone: the finished ones under Completed, the others under In progress.
  const mocks = useMocks();
  useSendWaiting(mocks);
  const examName = examTabs.find(t => t.key === exam)?.label || "";
  const mine = tab === "saved" ? [] : mocks.filter(m => (tab === "completed") === mockOver(m) && (!exam || m.exam === examName) && (!query || m.title.toLowerCase().includes(query.toLowerCase())));
  const items = withMocks(list.data?.items ?? [], mine);
  const local = { completed: mocks.filter(mockOver).length, progress: mocks.filter(m => !mockOver(m)).length, saved: 0 };

  const choose = (item: any) => setSelected((o) => (o.some((x) => x.id === item.id) ? o.filter((x) => x.id !== item.id) : o.length < 2 ? [...o, item] : o));
  async function compare() {
    setCmp({ open: true, busy: true });
    try {
      setCmp({ open: true, data: await post("/my/tests/compare", { left: selected[0].id, right: selected[1].id }) });
    } catch (e: any) {
      setCmp({ open: true, error: e.message });
    }
  }
  async function unsave(setId: string) {
    try {
      await del("/my/tests/saved/" + setId);
      list.reload();
    } catch {}
  }

  const renderItem = ({ item }: { item: any }) => {
    if (item.kind === "mock") return <MockCard m={item.mock} onOpen={() => router.push(`/misfire/mock/${item.mock.id}` as any)} />;
    if (tab === "saved") {
      return (
        <PaperCard testID={"saved-paper-" + item.set_id} faded={!item.available}>
          <View style={styles.statusRow}>
            <StatusLine testID={`saved-paper-status-${item.set_id}`} label="Saved" color={colors.custom_savedBlue} ink={colors.custom_tabInk} />
            <T testID={`saved-paper-meta-${item.set_id}`} size={11.5} color={colors.custom_tabInkSoft}>{item.exam} · saved {unixDate(item.saved_at)}</T>
          </View>
          <T testID={`saved-paper-title-${item.set_id}`} w="heavy" size={17} color={colors.custom_tabInk}>{item.title}</T>
          {!item.available ? <Notice tone="warning">{item.reason || "Unavailable right now."}</Notice> : null}
          <View style={styles.actions}>
            <Pill testID={"saved-remove-" + item.set_id} kind="outline" size="sm" label="Unsave" icon="bookmark-remove-outline" onPress={() => unsave(item.set_id)} />
            {item.available ? <Pill testID={"saved-open-" + item.set_id} size="sm" label="Open" iconRight="arrow-right" onPress={() => router.push(`/set/${item.set_id}`)} /> : null}
          </View>
        </PaperCard>
      );
    }
    const label = STATUS_LABEL[item.status] || item.status;
    const tone = learningStatusTone(item.status);
    // A scored paper's dot is royal blue: green is kept for completed All India days only.
    const dot = tone === "completed" ? colors.custom_royalMid : toneInk(tone);
    const picked = selected.some((x) => x.id === item.id);
    return (
      <PaperCard testID={`attempt-container-${item.id}`} chosen={picked}>
        <Press testID={"attempt-card-" + item.id} onPress={() => router.push(((item.resumable ? "/attempt/" : "/result/") + item.id) as any)} scaleTo={0.99} style={styles.attemptContent}>
          <View style={styles.statusRow}>
            <StatusLine testID={`attempt-status-${item.id}`} label={label} color={dot} ink={colors.custom_tabInk} />
            <T testID={`attempt-exam-${item.id}`} size={11.5} color={colors.custom_tabInkSoft}>{item.exam}</T>
          </View>
          <T testID={`attempt-title-${item.id}`} w="heavy" size={17} color={colors.custom_tabInk}>{item.title}</T>
          <T testID={`attempt-meta-${item.id}`} size={12} color={colors.custom_tabInkSoft}>
            Started {unixDate(item.started_at)} · {item.saved_answers}/{item.count} saved
            {item.remaining_seconds ? " · " + fmtClock(Math.round(item.remaining_seconds)) + " left" : ""}
          </T>
          {item.summary ? <T testID={`attempt-score-${item.id}`} w="heavy" size={15} color={item.summary.score < 0 ? colors.custom_chipBloodDeep : colors.custom_tabInk}>{item.summary.score} / {item.summary.maximum} marks{item.summary.accuracy != null ? ` · ${item.summary.accuracy}% accuracy` : ""}</T> : null}
        </Press>
        <View style={styles.actions}>
          {item.compare_eligible ? (
            <Press testID={"compare-select-" + item.id} onPress={() => choose(item)} accessibilityLabel="Select for comparison" accessibilityState={{ checked: picked }} style={[styles.compare, picked && { borderColor: colors.brandPrimary, backgroundColor: colors.custom_selectedOption }]}>
              <Icon name={picked ? "checkbox-marked-circle" : "checkbox-blank-circle-outline"} size={16} color={picked ? colors.brandText : colors.custom_tabInkSoft} />
              <T w="bold" size={12} color={colors.custom_tabInk}>Compare</T>
            </Press>
          ) : null}
          <Press testID={`attempt-action-label-${item.id}`} onPress={() => router.push(((item.resumable ? "/attempt/" : "/result/") + item.id) as any)} style={[styles.go, item.resumable ? { backgroundColor: colors.onSurface } : styles.goOutline]}>
            <T w="heavy" size={12.5} color={item.resumable ? colors.custom_bar : colors.custom_tabInk}>{item.resumable ? "Resume" : "Open result"}</T>
            <Icon name="arrow-right" size={15} color={item.resumable ? colors.custom_bar : colors.custom_tabInk} />
          </Press>
        </View>
      </PaperCard>
    );
  };

  return (
    // The tabs' shine rests while another tab or screen is in front.
    <ScreenMotion>
    <View testID="my-tests-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <View style={{ paddingHorizontal: space.lg, gap: space.md }}>
        <T testID="my-tests-title" w="heavy" size={28}>My Tests</T>
        {user?.access_type === "unverified_phone" ? <T size={11} color={colors.custom_eyebrow} testID="my-tests-identity-notice">This number’s profile is not a verified identity.</T> : null}
        <GlossTabs prefix="my-tests-tab" value={tab} onChange={(t) => { if (t !== tab) setSelected([]); setTab(t); }}
          items={TABS.map(t => ({ key: t, label: t === "progress" ? "In progress" : t === "saved" ? "Saved" : "Completed", look: TAB_LOOK[t], labelTestID: `my-tests-tab-label-${t}`,
            sub: list.data?.counts ? String((list.data.counts[t] || 0) + local[t]) : undefined, subTestID: `my-tests-count-${t}` }))} />
        <View style={styles.search}>
          <Icon name="magnify" size={20} color={colors.custom_eyebrow} />
          <TextInput testID="my-tests-search" value={q} onChangeText={setQ} placeholder="Search test names…" placeholderTextColor={colors.custom_dim} maxLength={100} style={[{ flex: 1, fontFamily: fonts.medium, fontSize: 14, color: colors.onSurface, paddingHorizontal: space.sm }, noOutline]} />
          {q ? <Press testID="my-tests-clear-search" onPress={() => setQ("")} accessibilityLabel="Clear search"><Icon name="close-circle" size={18} color={colors.custom_eyebrow} /></Press> : null}
        </View>
      </View>
      <View testID="my-tests-exam-filters" style={styles.filters}>
        <RedTabs prefix="my-tests-exam" value={exam} onChange={(k) => { if (k !== exam) setSelected([]); setExam(k); }} items={examTabs} />
      </View>
      {selected.length > 0 ? (
        <View style={{ paddingHorizontal: space.lg, paddingBottom: space.sm }}>
          <Pill testID="compare-attempts-button" kind="brand" label={`Compare ${selected.length}/2`} icon="compare-horizontal" disabled={selected.length !== 2} onPress={compare} />
        </View>
      ) : null}
      <FlatList
        data={items}
        keyExtractor={(x) => x.id}
        renderItem={renderItem}
        contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: (usesNativeTabs ? insets.bottom : 0) + space.xl, gap: space.md }}
        refreshControl={<RefreshControl testID="my-tests-refresh" refreshing={list.refreshing} onRefresh={list.reload} />}
        ListHeaderComponent={<>
          <ErrorBox error={list.error} retry={list.reload} testID="my-tests-error" />
          {tab === "completed" ? <T size={11} color={colors.custom_eyebrow} testID="my-tests-comparison-help">Select two attempts of the same paper and version to compare.</T> : null}
        </>}
        ListEmptyComponent={list.loading ? <View style={{ gap: space.md }}><Skeleton h={130} /><Skeleton h={130} /></View> : list.error ? <T testID="my-tests-unavailable" size={13} color={colors.muted}>Your tests could not be loaded. Your saved attempts have not been changed. Use Retry above.</T> : (
          <PaperCard testID="my-tests-empty"><Empty icon="bookmark-outline" title={query || exam ? "No tests match these filters." : tab === "saved" ? "Your next tests, kept here." : tab === "progress" ? "Ready for a fresh start?" : "Your journey starts with one attempt."} body={tab === "saved" ? "Tap Save on any paper. It won’t start an attempt." : "Existing attempts appear here automatically."} action={<Pill testID="my-tests-discover" label="Explore exams" iconRight="arrow-right" onPress={() => router.push("/(tabs)")} />} /></PaperCard>
        )}
      />
      <DSheet visible={cmp.open} onClose={() => setCmp({ open: false })} testID="compare-sheet" title="Attempt comparison">
        {cmp.busy ? <Skeleton h={120} /> : null}
        <ErrorBox error={cmp.error} />
        {cmp.data ? (
          <View style={{ gap: space.sm }}>
            <T size={13} w="bold">Score change: {cmp.data.score_delta > 0 ? "+" : ""}{cmp.data.score_delta}{cmp.data.accuracy_delta != null ? ` · Accuracy ${cmp.data.accuracy_delta > 0 ? "+" : ""}${cmp.data.accuracy_delta}%` : ""}</T>
            {cmp.data.subjects?.map((s: any) => (
              <View key={s.name} style={{ flexDirection: "row", justifyContent: "space-between" }}>
                <T size={13}>{s.name}</T>
                <T w="bold" size={13}>{s.before?.score ?? "—"} → {s.after?.score ?? "—"}</T>
              </View>
            ))}
            <T size={11} color={colors.custom_eyebrow}>{cmp.data.basis}</T>
          </View>
        ) : null}
        <Pill testID="compare-close" kind="outline" label="Close" onPress={() => setCmp({ open: false })} />
      </DSheet>
    </View>
    </ScreenMotion>
  );
}

const styles = StyleSheet.create({
  // Home's exam card: white into the softest grey with a hairline round it. A card picked for Compare has a 2-point red
  // line (and 1 less padding, so it keeps its size).
  paper: { padding: 18, gap: space.sm, borderRadius: 24, borderWidth: 1, borderColor: colors.custom_cardLineStrong, overflow: "hidden" },
  paperOn: { padding: 17, borderWidth: 2, borderColor: colors.brandPrimary },
  faded: { opacity: 0.75 },
  statusRow: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: space.sm },
  attemptContent: { gap: space.sm },
  actions: { flexDirection: "row", flexWrap: "wrap", justifyContent: "flex-end", gap: space.sm, alignItems: "center", marginTop: space.xs },
  // White chips with a hairline, as the icon circle on Home's exam cards.
  compare: { flexDirection: "row", alignItems: "center", gap: 5, paddingHorizontal: 14, minHeight: 44, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card },
  go: { flexDirection: "row", alignItems: "center", gap: 5, paddingHorizontal: 16, minHeight: 44, borderRadius: radius.pill },
  goOutline: { borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card },
  search: { flexDirection: "row", alignItems: "center", backgroundColor: colors.custom_cardRaised, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLine, paddingHorizontal: space.lg, height: 48 },
  filters: { paddingHorizontal: space.lg, paddingVertical: space.md },
});
