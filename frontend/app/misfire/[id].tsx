// One paper's Misfire: the questions of this paper that went wrong or were left, by subject. Reached from a test
// family's tab. Any of them opens to be solved again; the paper's full analysis (with Solutions) is one tap away.
import React, { useMemo, useState } from "react";
import { FlatList, StyleSheet, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { RawResult, apiRaw } from "@/src/api/client";
import { resultIsReleased } from "@/src/assets/paperAssets";
import { originalLook } from "@/src/assets/pieces";
import { useCached } from "@/src/useCached";
import { Empty, ErrorBox, Skeleton, T } from "@/src/components/ui";
import { DCard, Pill, ScreenHeader } from "@/src/components/design";
import { colors, space } from "@/src/theme";
import { MisfireItem, fromResult, getFixedIds, misfireKey } from "@/src/misfire/api";
import { PillRow, QuestionRow } from "@/src/misfire/parts";
import { applied, misfireAccount, openQueue, usePatches } from "@/src/misfire/store";

export default function MisfirePaper() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  if (user) misfireAccount(user.id);
  usePatches();
  // The result is too large for the phone's small list cache: it is read afresh each time this paper is opened.
  const res = useCached<RawResult<any>>(user && id ? `${misfireKey(user.id)}.paper.${id}` : null,
    async signal => { const r = await apiRaw<any>(`/attempts/${encodeURIComponent(id!)}/results?score_version=original`, { signal }); originalLook(r.data); return r; }, false);
  const fixed = useCached<string[]>(user ? `${misfireKey(user.id)}.fixedids` : null, getFixedIds, false);
  const [subject, setSubject] = useState("");
  const [outcome, setOutcome] = useState("");
  const r = res.data?.data, ready = !!res.data && resultIsReleased(res.data.status, r);
  const all = useMemo<MisfireItem[]>(() => {
    if (!ready) return [];
    const done = new Set(fixed.data || []);
    return (r.questions || []).filter((q: any) => q.outcome === "incorrect" || q.outcome === "skipped").map((q: any) => fromResult(r, q, done.has(`${r.id}:${q.id}`)));
  }, [ready, r, fixed.data]);
  const items = all.map(applied);
  const subjects = [...new Set(items.map(i => i.subject))];
  const rows = items.filter(i => (!subject || i.subject === subject) && (!outcome || i.outcome === outcome));
  const count = (o: string) => items.filter(i => (!subject || i.subject === subject) && i.outcome === o).length;
  const understood = items.filter(i => i.status === "fixed").length;
  const open = (index: number) => { openQueue(rows, index); router.push("/misfire/solve" as any); };
  const firstOpen = rows.findIndex(i => i.status === "open");
  const back = () => (router.canGoBack() ? router.back() : router.replace("/misfire" as any));

  return <View testID="misfire-paper-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
    <ScreenHeader testID="misfire-paper-header" title={r?.title || "Is paper ki galtiyan"} eyebrow="Misfire · is paper ki galtiyan" backTestID="misfire-paper-back" onBack={back} />
    <FlatList testID="misfire-paper-list" data={rows} keyExtractor={i => i.id} initialNumToRender={12} windowSize={7}
      contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: insets.bottom + space.xxl, gap: space.sm }}
      refreshing={res.refreshing} onRefresh={() => { res.reload(); fixed.reload(); }}
      ListHeaderComponent={<View style={{ gap: space.md, paddingBottom: space.sm }}>
        <ErrorBox error={res.error && !res.data ? res.error : ""} retry={res.reload} testID="misfire-paper-error" />
        {!res.data && !res.error ? <View testID="misfire-paper-loading" style={{ gap: space.sm }}><Skeleton h={96} /><Skeleton h={58} /><Skeleton h={58} /></View> : null}
        {res.data && !ready ? <DCard testID="misfire-paper-sealed"><Empty icon="lock-clock" title="Is paper ka result abhi nahi khula." body="Result khulte hi iske galat aur chhode sawaal yahan aa jayenge." /></DCard> : null}
        {ready ? <>
          <DCard testID="misfire-paper-summary" style={{ gap: space.md }}>
            <T testID="misfire-paper-counts" size={13.5} color={colors.custom_softText}>
              <T w="heavy" size={13.5} color={colors.error}>{items.filter(i => i.outcome === "incorrect").length} galat</T> · <T w="heavy" size={13.5} color={colors.warning}>{items.filter(i => i.outcome === "skipped").length} chhode</T> · <T w="heavy" size={13.5} color={colors.success}>{understood} samajh gaya</T>
            </T>
            <View style={styles.actions}>
              {firstOpen >= 0 ? <Pill testID="misfire-paper-start" kind="brand" size="sm" icon="play" label="Dobara solve karo" style={{ flexGrow: 1 }} onPress={() => open(firstOpen)} /> : null}
              <Pill testID="misfire-paper-analysis" kind="outline" size="sm" icon="chart-donut" label="Poora analysis" style={{ flexGrow: 1 }} onPress={() => router.push(`/result/${id}` as any)} />
            </View>
          </DCard>
          {subjects.length > 1 ? <PillRow prefix="misfire-paper-subject" value={subject} onChange={setSubject} items={[{ key: "", label: "Sab", count: items.length }, ...subjects.map(s => ({ key: s, label: s, count: items.filter(i => i.subject === s).length }))]} /> : null}
          <PillRow prefix="misfire-paper-outcome" value={outcome} onChange={setOutcome} items={[{ key: "", label: "Galat + chhode" }, { key: "incorrect", label: "Galat", count: count("incorrect") }, { key: "skipped", label: "Chhode", count: count("skipped") }]} />
        </> : null}
      </View>}
      renderItem={({ item, index }) => <QuestionRow testID={`misfire-paper-row-${index}`} item={item} onPress={() => open(index)} />}
      ListEmptyComponent={ready ? <DCard testID="misfire-paper-empty"><Empty icon="check-circle-outline" title={items.length ? "Is filter mein koi sawaal nahi." : "Is paper mein koi galti nahi."} body={items.length ? "Upar se doosra filter chuno." : "Saare sawaal sahi the."} /></DCard> : undefined} />
  </View>;
}

const styles = StyleSheet.create({
  actions: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
});
