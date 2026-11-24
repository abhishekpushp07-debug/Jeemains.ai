// A test family's tab (AITS, JEE Chapter-wise, BITSAT Mocks…): its finished papers, newest first, each with how many
// questions went wrong or were left. A paper opens its own Misfire list.
import React from "react";
import { FlatList, RefreshControl, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Empty, ErrorBox, Icon, Press, Skeleton, T } from "@/src/components/ui";
import { DCard, Pill } from "@/src/components/design";
import { ToneTag } from "@/src/analysis/parts";
import { colors, space } from "@/src/theme";
import { istDate, unixDate } from "@/src/navigation";
import { Family, Paper, PaperPage, misfireKey } from "./api";
import { usePaged } from "./usePaged";

export function PapersTab({ uid, family }: { uid: string; family: Family }) {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const list = usePaged<Paper, PaperPage>(`${misfireKey(uid)}.papers.${family.key}`, family.load);
  // Only a paper whose result is out has mistakes to show; one still running or sealed appears after its result.
  const papers = list.items.filter(p => !!p.summary);
  return <FlatList testID={`misfire-papers-${family.key}`} data={papers} keyExtractor={p => p.id} initialNumToRender={8} windowSize={7}
    contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: insets.bottom + space.xxl, gap: space.md }}
    refreshControl={<RefreshControl refreshing={false} onRefresh={list.reload} />}
    ListHeaderComponent={<ErrorBox error={list.error && !list.first ? list.error : ""} retry={list.reload} testID="misfire-papers-error" />}
    renderItem={({ item: p }) => {
      const s = p.summary, wrong = s.incorrect || 0, skipped = s.skipped || 0, misses = wrong + skipped;
      const when = p.series_date ? istDate(p.series_date) : unixDate(p.submitted_at || p.started_at);
      const kind = p.mode === "series_live" ? " · LIVE" : p.mode === "series_practice" ? " · PRACTICE" : "";
      return <Press testID={`misfire-paper-${p.id}`} disabled={!misses} onPress={() => router.push(`/misfire/${p.id}` as any)} scaleTo={0.99}
        accessibilityLabel={`${p.title}. ${wrong} galat, ${skipped} chhode.${misses ? " Galtiyan kholo" : ""}`}>
        <DCard style={{ gap: space.sm }}>
          <T w="heavy" size={10} color={colors.custom_eyebrow} style={styles.caps}>{`${when}${kind}`.toUpperCase()}</T>
          <View style={styles.top}>
            <T testID={`misfire-paper-title-${p.id}`} w="heavy" size={16} numberOfLines={2} style={{ flex: 1 }}>{p.title}</T>
            <T w="mono" size={15}>{s.score}<T w="monoRegular" size={12} color={colors.muted}>/{s.maximum}</T></T>
          </View>
          <View style={styles.bottom}>
            <View style={styles.tags}>
              <ToneTag label={`${wrong} galat`} tone={wrong ? "bad" : "mute"} icon="close" />
              <ToneTag label={`${skipped} chhode`} tone={skipped ? "warn" : "mute"} icon="minus" />
            </View>
            {misses ? <View style={styles.go}><T testID={`misfire-paper-open-${p.id}`} w="heavy" size={12.5} color={colors.brandText}>Galtiyan kholo</T><Icon name="arrow-right" size={15} color={colors.brandText} /></View>
              : <T size={12} w="bold" color={colors.success}>Koi galti nahi</T>}
          </View>
        </DCard>
      </Press>;
    }}
    ListEmptyComponent={list.loading && !list.first ? <View testID="misfire-papers-loading" style={{ gap: space.md }}><Skeleton h={120} /><Skeleton h={120} /></View>
      : list.first && !list.hasMore ? <DCard testID="misfire-papers-empty"><Empty icon="file-document-outline" title="Is section mein abhi koi paper nahi." body={family.empty} /></DCard> : undefined}
    ListFooterComponent={<View style={{ gap: space.sm }}>
      <ErrorBox error={list.moreError} testID="misfire-papers-more-error" />
      {list.hasMore ? <Pill testID="misfire-papers-more" kind="outline" label="Aur papers dikhao" busy={list.busy} onPress={list.more} /> : null}
    </View>} />;
}

const styles = StyleSheet.create({
  caps: { letterSpacing: 1.4 },
  top: { flexDirection: "row", alignItems: "flex-start", gap: space.md },
  bottom: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: space.sm },
  tags: { flexDirection: "row", alignItems: "center", gap: 6 },
  go: { minHeight: 32, flexDirection: "row", alignItems: "center", gap: 4 },
});
