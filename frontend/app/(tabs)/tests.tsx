import React, { useEffect, useState } from "react";
import { FlatList, RefreshControl, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { api, del, post } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { Button, Card, Chip, Empty, ErrorBox, Icon, Notice, Press, Sheet, Skeleton, T } from "@/src/components/ui";
import { colors, fonts, radius, space } from "@/src/theme";
import { fmtClock, unixDate, usesNativeTabs } from "@/src/navigation";

type Tab = "progress" | "saved" | "completed";
const STATUS: Record<Tab, [string, string][]> = {
  progress: [["all", "All ongoing"]],
  saved: [["all", "All"], ["available", "Available"], ["unavailable", "Unavailable"]],
  completed: [["all", "All outcomes"], ["completed", "Scored"], ["expired", "Time expired"], ["grading", "Preparing"], ["embargoed", "Sealed"]],
};
const STATUS_LABEL: Record<string, [string, string]> = {
  active: ["In progress", colors.success], expired: ["Time expired · finish grading", colors.warning], embargoed: ["Result sealed", colors.custom_series], completed: ["Scored", colors.brandPrimary], grading: ["Preparing result", colors.custom_amber],
};
// Kept at module level so returning to this tab restores the same view.
const memo = { tab: "progress" as Tab, q: "", status: "all", exam: "" };

export default function MyTests() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>(memo.tab);
  const [q, setQ] = useState(memo.q);
  const [query, setQuery] = useState(memo.q);
  const [status, setStatus] = useState(memo.status);
  const [exam, setExam] = useState(memo.exam);
  const [selected, setSelected] = useState<any[]>([]);
  const [cmp, setCmp] = useState<{ open: boolean; data?: any; error?: string; busy?: boolean }>({ open: false });
  Object.assign(memo, { tab, q: query, status, exam });
  useEffect(() => {
    const t = setTimeout(() => setQuery(q.trim()), 300);
    return () => clearTimeout(t);
  }, [q]);
  useEffect(() => setSelected([]), [tab, exam]);
  const params = new URLSearchParams({ tab, page: "1", q: query, status, exam }).toString();
  const list = useCached<any>(user ? `u.${user.id}.tests.${params}` : null, (signal) => api("/my/tests?" + params, { signal }));

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
        <Card testID={"saved-paper-" + item.set_id} style={{ gap: 6, opacity: item.available ? 1 : 0.75 }}>
          <T w="bold" size={11} color={colors.muted}>{item.exam} · saved {unixDate(item.saved_at)}</T>
          <T w="heavy" size={16}>{item.title}</T>
          {!item.available ? <Notice tone="warning">{item.reason || "Unavailable right now."}</Notice> : null}
          <View style={{ flexDirection: "row", gap: space.sm }}>
            {item.available ? <Button testID={"saved-open-" + item.set_id} label="Open" style={{ flex: 1 }} onPress={() => router.push(`/set/${item.set_id}`)} /> : null}
            <Button testID={"saved-remove-" + item.set_id} kind="secondary" label="Unsave" icon="bookmark-remove-outline" style={{ flex: 1 }} onPress={() => unsave(item.set_id)} />
          </View>
        </Card>
      );
    }
    const [label, tone] = STATUS_LABEL[item.status] || [item.status, colors.muted];
    const picked = selected.some((x) => x.id === item.id);
    return (
      <Press testID={"attempt-card-" + item.id} onPress={() => router.push(((item.resumable ? "/attempt/" : "/result/") + item.id) as any)}>
        <Card style={{ gap: 6, borderColor: picked ? colors.brandPrimary : colors.border }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
            <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: tone }} />
            <T w="bold" size={12} color={tone}>{label}</T>
            <T size={12} color={colors.muted}>· {item.exam}</T>
          </View>
          <T w="heavy" size={16}>{item.title}</T>
          <T size={12} color={colors.muted}>
            Started {unixDate(item.started_at)} · {item.saved_answers}/{item.count} saved
            {item.remaining_seconds ? " · " + fmtClock(Math.round(item.remaining_seconds)) + " left" : ""}
          </T>
          {item.summary ? <T w="heavy" size={15} color={colors.brandPrimary}>{item.summary.score} / {item.summary.maximum} marks{item.summary.accuracy != null ? ` · ${item.summary.accuracy}% accuracy` : ""}</T> : null}
          <View style={{ flexDirection: "row", gap: space.sm, alignItems: "center" }}>
            <T w="bold" size={13} color={colors.brandPrimary}>{item.resumable ? "Resume exact attempt →" : "Open result →"}</T>
            <View style={{ flex: 1 }} />
            {item.compare_eligible ? (
              <Press testID={"compare-select-" + item.id} onPress={() => choose(item)} accessibilityLabel="Select for comparison" style={{ flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 10, height: 36, borderRadius: radius.pill, borderWidth: 1, borderColor: picked ? colors.brandPrimary : colors.border, backgroundColor: picked ? colors.custom_infoSoft : colors.surfaceSecondary }}>
                <Icon name={picked ? "checkbox-marked" : "checkbox-blank-outline"} size={16} color={colors.brandPrimary} />
                <T w="bold" size={12}>Compare</T>
              </Press>
            ) : null}
          </View>
        </Card>
      </Press>
    );
  };

  return (
    <View testID="my-tests-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <View style={{ paddingHorizontal: space.lg, gap: space.sm }}>
        <T w="heavy" size={26}>My Tests</T>
        {user?.access_type === "unverified_phone" ? <T size={11} color={colors.muted} testID="my-tests-identity-notice">This number’s profile is not a verified identity.</T> : null}
        <View style={{ flexDirection: "row", gap: space.sm }}>
          {(["progress", "saved", "completed"] as Tab[]).map((t) => (
            <Press key={t} testID={"my-tests-tab-" + t} onPress={() => { setTab(t); setStatus("all"); }} style={{ flex: 1, height: 44, borderRadius: radius.md, alignItems: "center", justifyContent: "center", backgroundColor: tab === t ? colors.surfaceInverse : colors.surfaceSecondary, borderWidth: 1, borderColor: tab === t ? colors.surfaceInverse : colors.border }}>
              <T w="heavy" size={13} color={tab === t ? colors.onSurfaceInverse : colors.onSurface}>{t === "progress" ? "In progress" : t === "saved" ? "Saved" : "Completed"} {list.data?.counts ? `· ${list.data.counts[t]}` : ""}</T>
            </Press>
          ))}
        </View>
        <View style={{ flexDirection: "row", alignItems: "center", backgroundColor: colors.surfaceSecondary, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, paddingHorizontal: space.md, height: 46 }}>
          <Icon name="magnify" size={20} color={colors.muted} />
          <TextInput testID="my-tests-search" value={q} onChangeText={setQ} placeholder="Search test names…" placeholderTextColor={colors.muted} maxLength={100} style={{ flex: 1, fontFamily: fonts.medium, fontSize: 14, color: colors.onSurface, paddingHorizontal: space.sm }} />
        </View>
      </View>
      <View style={{ height: 56, justifyContent: "center" }}>
        <FlatList horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: space.sm, paddingHorizontal: space.lg, alignItems: "center" }}
          data={[...STATUS[tab].map(([v, l]) => ({ k: "s" + v, v, l, kind: "status" })), ...["", "JEE Main", "BITSAT", "COMEDK"].map((e) => ({ k: "e" + e, v: e, l: e || "All exams", kind: "exam" }))]}
          keyExtractor={(x) => x.k}
          renderItem={({ item }) => <Chip testID={`my-tests-${item.kind}-${item.v || "all"}`} label={item.l} active={item.kind === "status" ? status === item.v : exam === item.v} color={item.kind === "exam" ? colors.custom_series : colors.brandPrimary} onPress={() => (item.kind === "status" ? setStatus(item.v) : setExam(item.v))} />}
        />
      </View>
      {selected.length > 0 ? (
        <View style={{ paddingHorizontal: space.lg, paddingBottom: space.sm }}>
          <Button testID="compare-attempts-button" label={`Compare ${selected.length}/2`} icon="compare-horizontal" disabled={selected.length !== 2} onPress={compare} />
        </View>
      ) : null}
      <FlatList
        data={list.data?.items ?? []}
        keyExtractor={(x) => x.id}
        renderItem={renderItem}
        contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: (usesNativeTabs ? insets.bottom : 0) + space.xl, gap: space.md }}
        refreshControl={<RefreshControl refreshing={false} onRefresh={list.reload} />}
        ListHeaderComponent={<>
          <ErrorBox error={list.error} retry={list.reload} testID="my-tests-error" />
          {tab === "completed" ? <T size={11} color={colors.muted} testID="my-tests-comparison-help">Select two attempts of the same paper and version to compare.</T> : null}
        </>}
        ListEmptyComponent={list.loading ? <View style={{ gap: space.md }}><Skeleton h={110} /><Skeleton h={110} /></View> : (
          <Card testID="my-tests-empty"><Empty icon="bookmark-outline" title={query || exam || status !== "all" ? "No tests match these filters." : tab === "saved" ? "Your next tests, kept here." : tab === "progress" ? "Ready for a fresh start?" : "Your journey starts with one attempt."} body={tab === "saved" ? "Tap Save on any paper. It won’t start an attempt." : "Existing attempts appear here automatically."} action={<Button testID="my-tests-discover" label="Explore exams" onPress={() => router.push("/(tabs)")} />} /></Card>
        )}
      />
      <Sheet visible={cmp.open} onClose={() => setCmp({ open: false })} testID="compare-sheet">
        <T w="heavy" size={20}>Attempt comparison</T>
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
            <T size={11} color={colors.muted}>{cmp.data.basis}</T>
          </View>
        ) : null}
        <Button testID="compare-close" kind="secondary" label="Close" onPress={() => setCmp({ open: false })} />
      </Sheet>
    </View>
  );
}
