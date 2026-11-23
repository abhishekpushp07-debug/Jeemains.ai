import React, { useEffect, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, TextInput, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { api, del, post } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { useListFocus } from "@/src/useListFocus";
import { Chip, Empty, ErrorBox, Icon, Notice, Press, Skeleton, T } from "@/src/components/ui";
import { DCard, DSheet, Pill, StatusLine } from "@/src/components/design";
import { GlossTabs, TabLook } from "@/src/components/GlossTabs";
import { ScreenMotion } from "@/src/motion";
import { toneInk } from "@/src/components/PyqPaperCard";
import { colors, fonts, noOutline, radius, space, tabEdges } from "@/src/theme";
import { learningStatusTone } from "@/src/components/LearningTheme";
import { EXAMS, fmtClock, unixDate, usesNativeTabs } from "@/src/navigation";
import { useExams } from "@/src/api/examCatalog";

const EXAM_FILTERS = EXAMS.map(e => ({ key: e.name, name: e.name }));

type Tab = "progress" | "saved" | "completed";
const TABS: Tab[] = ["completed", "progress", "saved"];
// Each tab keeps its own colour (baby pink, yellow, sky blue): full when open, a softer wash when not, with an edge from its own family.
const TAB_LOOK: Record<Tab, TabLook> = {
  completed: { on: [colors.custom_tabPink, colors.custom_tabPinkDeep], rest: [colors.custom_tabPinkSoft, colors.custom_tabPinkSoftDeep], edge: tabEdges.pink, glow: colors.custom_tabPinkGlow },
  progress: { on: [colors.custom_tabSun, colors.custom_tabSunDeep], rest: [colors.custom_tabSunSoft, colors.custom_tabSunSoftDeep], edge: tabEdges.sun, glow: colors.custom_tabSunGlow },
  saved: { on: [colors.custom_tabSky, colors.custom_tabSkyDeep], rest: [colors.custom_tabSkySoft, colors.custom_tabSkySoftDeep], edge: tabEdges.sky, glow: colors.custom_tabSkyGlow },
};
const STATUS: Record<Tab, [string, string][]> = {
  progress: [["all", "All ongoing"]],
  saved: [["all", "All"], ["available", "Available"], ["unavailable", "Unavailable"]],
  completed: [["all", "All outcomes"], ["completed", "Scored"], ["expired", "Time expired"], ["grading", "Preparing"], ["embargoed", "Sealed"]],
};
const STATUS_LABEL: Record<string, string> = {
  active: "In progress", expired: "Time expired · finish grading", embargoed: "Result sealed", completed: "Scored", grading: "Preparing result",
};
// Kept at module level so returning to this tab restores the same view.
const memo = { tab: "completed" as Tab, q: "", status: "all", exam: "" };

export default function MyTests() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const params = useLocalSearchParams<{ tab?: string; at?: string }>();
  const [tab, setTab] = useState<Tab>(memo.tab);
  const [q, setQ] = useState(memo.q);
  const [query, setQuery] = useState(memo.q);
  const [status, setStatus] = useState(memo.status);
  const [exam, setExam] = useState(memo.exam);
  const [selected, setSelected] = useState<any[]>([]);
  const [cmp, setCmp] = useState<{ open: boolean; data?: any; error?: string; busy?: boolean }>({ open: false });
  Object.assign(memo, { tab, q: query, status, exam });
  // Home stat cards open this screen on a chosen tab.
  useEffect(() => {
    if (params.tab && (TABS as string[]).includes(params.tab)) { setTab(params.tab as Tab); setStatus("all"); setSelected([]); }
  }, [params.tab, params.at]);
  useEffect(() => {
    const t = setTimeout(() => setQuery(q.trim()), 300);
    return () => clearTimeout(t);
  }, [q]);
  const search = new URLSearchParams({ tab, page: "1", q: query, status, exam }).toString();
  const list = useCached<any>(user ? `u.${user.id}.tests.${search}` : null, (signal) => api("/my/tests?" + search, { signal }));
  useListFocus(list.revalidate);
  // Exam filters follow the website's exam list, so attempts of a newly added exam can be filtered too.
  const catalog = useExams();
  useListFocus(catalog.revalidate);
  // An exam the owner has hidden cannot stay selected: the website refuses that filter.
  const examKeys = catalog.exams?.map(e => e.key).join("|");
  useEffect(() => { if (exam && examKeys !== undefined && !examKeys.split("|").includes(exam)) setExam(""); }, [exam, examKeys]);

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
    if (tab === "saved") {
      return (
        <DCard testID={"saved-paper-" + item.set_id} style={[styles.paper, { opacity: item.available ? 1 : 0.75 }]}>
          <View style={styles.statusRow}>
            <StatusLine testID={`saved-paper-status-${item.set_id}`} label="Saved" color={colors.custom_savedBlue} />
            <T testID={`saved-paper-meta-${item.set_id}`} size={11.5} color={colors.custom_eyebrow}>{item.exam} · saved {unixDate(item.saved_at)}</T>
          </View>
          <T testID={`saved-paper-title-${item.set_id}`} w="heavy" size={17}>{item.title}</T>
          {!item.available ? <Notice tone="warning">{item.reason || "Unavailable right now."}</Notice> : null}
          <View style={styles.actions}>
            <Pill testID={"saved-remove-" + item.set_id} kind="outline" size="sm" label="Unsave" icon="bookmark-remove-outline" onPress={() => unsave(item.set_id)} />
            {item.available ? <Pill testID={"saved-open-" + item.set_id} size="sm" label="Open" iconRight="arrow-right" onPress={() => router.push(`/set/${item.set_id}`)} /> : null}
          </View>
        </DCard>
      );
    }
    const label = STATUS_LABEL[item.status] || item.status;
    const tone = learningStatusTone(item.status);
    const ink = toneInk(tone);
    const picked = selected.some((x) => x.id === item.id);
    return (
      <DCard testID={`attempt-container-${item.id}`} style={[styles.paper, picked && { borderColor: colors.brandPrimary }]}>
        <Press testID={"attempt-card-" + item.id} onPress={() => router.push(((item.resumable ? "/attempt/" : "/result/") + item.id) as any)} scaleTo={0.99} style={styles.attemptContent}>
          <View style={styles.statusRow}>
            <StatusLine testID={`attempt-status-${item.id}`} label={label} color={ink} />
            <T testID={`attempt-exam-${item.id}`} size={11.5} color={colors.custom_eyebrow}>{item.exam}</T>
          </View>
          <T testID={`attempt-title-${item.id}`} w="heavy" size={17}>{item.title}</T>
          <T testID={`attempt-meta-${item.id}`} size={12} color={colors.muted}>
            Started {unixDate(item.started_at)} · {item.saved_answers}/{item.count} saved
            {item.remaining_seconds ? " · " + fmtClock(Math.round(item.remaining_seconds)) + " left" : ""}
          </T>
          {item.summary ? <T testID={`attempt-score-${item.id}`} w="heavy" size={15} color={item.summary.score < 0 ? colors.error : item.summary.score > 0 ? colors.custom_mint : colors.onSurface}>{item.summary.score} / {item.summary.maximum} marks{item.summary.accuracy != null ? ` · ${item.summary.accuracy}% accuracy` : ""}</T> : null}
        </Press>
        <View style={styles.actions}>
          {item.compare_eligible ? (
            <Press testID={"compare-select-" + item.id} onPress={() => choose(item)} accessibilityLabel="Select for comparison" accessibilityState={{ checked: picked }} style={[styles.compare, picked && { borderColor: colors.brandPrimary, backgroundColor: colors.custom_selectedOption }]}>
              <Icon name={picked ? "checkbox-marked-circle" : "checkbox-blank-circle-outline"} size={16} color={picked ? colors.brandText : colors.muted} />
              <T w="bold" size={12}>Compare</T>
            </Press>
          ) : null}
          <Press testID={`attempt-action-label-${item.id}`} onPress={() => router.push(((item.resumable ? "/attempt/" : "/result/") + item.id) as any)} style={[styles.go, item.resumable ? { backgroundColor: colors.onSurface } : styles.goOutline]}>
            <T w="heavy" size={12.5} color={item.resumable ? colors.custom_bar : colors.onSurface}>{item.resumable ? "Resume" : "Open result"}</T>
            <Icon name="arrow-right" size={15} color={item.resumable ? colors.custom_bar : colors.onSurface} />
          </Press>
        </View>
      </DCard>
    );
  };

  return (
    <View testID="my-tests-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <View style={{ paddingHorizontal: space.lg, gap: space.md }}>
        <T testID="my-tests-title" w="heavy" size={28}>My Tests</T>
        {user?.access_type === "unverified_phone" ? <T size={11} color={colors.custom_eyebrow} testID="my-tests-identity-notice">This number’s profile is not a verified identity.</T> : null}
        {/* The tabs' shine rests while another tab or screen is in front. */}
        <ScreenMotion><GlossTabs prefix="my-tests-tab" value={tab} onChange={(t) => { if (t !== tab) setSelected([]); setTab(t); setStatus("all"); }}
          items={TABS.map(t => ({ key: t, label: t === "progress" ? "In progress" : t === "saved" ? "Saved" : "Completed", look: TAB_LOOK[t], labelTestID: `my-tests-tab-label-${t}`,
            sub: list.data?.counts ? String(list.data.counts[t]) : undefined, subTestID: `my-tests-count-${t}` }))} /></ScreenMotion>
        <View style={styles.search}>
          <Icon name="magnify" size={20} color={colors.custom_eyebrow} />
          <TextInput testID="my-tests-search" value={q} onChangeText={setQ} placeholder="Search test names…" placeholderTextColor={colors.custom_dim} maxLength={100} style={[{ flex: 1, fontFamily: fonts.medium, fontSize: 14, color: colors.onSurface, paddingHorizontal: space.sm }, noOutline]} />
          {q ? <Press testID="my-tests-clear-search" onPress={() => setQ("")} accessibilityLabel="Clear search"><Icon name="close-circle" size={18} color={colors.custom_eyebrow} /></Press> : null}
        </View>
      </View>
      <View style={{ height: 60, justifyContent: "center" }}>
        <FlatList horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: space.sm, paddingHorizontal: space.lg, alignItems: "center" }}
          data={[...STATUS[tab].map(([v, l]) => ({ k: "s" + v, v, l, kind: "status" })), { k: "divider", v: "", l: "", kind: "divider" }, ...[{ key: "", name: "All exams" }, ...(catalog.exams ?? EXAM_FILTERS)].map((e) => ({ k: "e" + e.key, v: e.key, l: e.name, kind: "exam" }))]}
          keyExtractor={(x) => x.k}
          renderItem={({ item }) => item.kind === "divider" ? <View style={styles.chipDivider} /> : <Chip testID={`my-tests-${item.kind}-${item.v || "all"}`} label={item.l} active={item.kind === "status" ? status === item.v : exam === item.v} onPress={() => { if (item.kind === "status") setStatus(item.v); else { if (item.v !== exam) setSelected([]); setExam(item.v); } }} />}
        />
      </View>
      {selected.length > 0 ? (
        <View style={{ paddingHorizontal: space.lg, paddingBottom: space.sm }}>
          <Pill testID="compare-attempts-button" kind="brand" label={`Compare ${selected.length}/2`} icon="compare-horizontal" disabled={selected.length !== 2} onPress={compare} />
        </View>
      ) : null}
      <FlatList
        data={list.data?.items ?? []}
        keyExtractor={(x) => x.id}
        renderItem={renderItem}
        contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: (usesNativeTabs ? insets.bottom : 0) + space.xl, gap: space.md }}
        refreshControl={<RefreshControl testID="my-tests-refresh" refreshing={list.refreshing} onRefresh={list.reload} />}
        ListHeaderComponent={<>
          <ErrorBox error={list.error} retry={list.reload} testID="my-tests-error" />
          {tab === "completed" ? <T size={11} color={colors.custom_eyebrow} testID="my-tests-comparison-help">Select two attempts of the same paper and version to compare.</T> : null}
        </>}
        ListEmptyComponent={list.loading ? <View style={{ gap: space.md }}><Skeleton h={130} /><Skeleton h={130} /></View> : list.error ? <T testID="my-tests-unavailable" size={13} color={colors.muted}>Your tests could not be loaded. Your saved attempts have not been changed. Use Retry above.</T> : (
          <DCard testID="my-tests-empty"><Empty icon="bookmark-outline" title={query || exam || status !== "all" ? "No tests match these filters." : tab === "saved" ? "Your next tests, kept here." : tab === "progress" ? "Ready for a fresh start?" : "Your journey starts with one attempt."} body={tab === "saved" ? "Tap Save on any paper. It won’t start an attempt." : "Existing attempts appear here automatically."} action={<Pill testID="my-tests-discover" label="Explore exams" iconRight="arrow-right" onPress={() => router.push("/(tabs)")} />} /></DCard>
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
  );
}

const styles = StyleSheet.create({
  paper: { padding: 18, borderRadius: 22, gap: space.sm, overflow: "hidden" },
  statusRow: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: space.sm },
  attemptContent: { gap: space.sm },
  actions: { flexDirection: "row", flexWrap: "wrap", justifyContent: "flex-end", gap: space.sm, alignItems: "center", marginTop: space.xs },
  compare: { flexDirection: "row", alignItems: "center", gap: 5, paddingHorizontal: 14, minHeight: 44, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised },
  go: { flexDirection: "row", alignItems: "center", gap: 5, paddingHorizontal: 16, minHeight: 44, borderRadius: radius.pill },
  goOutline: { borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised },
  search: { flexDirection: "row", alignItems: "center", backgroundColor: colors.custom_cardRaised, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLine, paddingHorizontal: space.lg, height: 48 },
  chipDivider: { width: 1, height: 24, marginHorizontal: 4, backgroundColor: colors.custom_cardLineStrong },
});
