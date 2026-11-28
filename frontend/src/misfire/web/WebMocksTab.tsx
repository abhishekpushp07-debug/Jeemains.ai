// Misfire's "Mock" tab, shown only while the website's switch "misfire" is on (src/misfire/web.ts): make a new Misfire
// Mock on jeelive.ai, and every one made (newest first), started and finished in the app or on the website alike.
import React from "react";
import { FlatList, RefreshControl, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Empty, ErrorBox, Icon, Press, Skeleton, T } from "@/src/components/ui";
import { DCard, Pill } from "@/src/components/design";
import { ToneTag } from "@/src/analysis/parts";
import { colors, space } from "@/src/theme";
import { unixDate } from "@/src/navigation";
import { useListFocus } from "@/src/useListFocus";
import { ChoiceHero, ON_HERO, heroStyles } from "@/src/choice/looks";
import { usePaged } from "../usePaged";
import { WebMock, loadWebMocks, webMockPath, webMocksKey } from "../web";

function WebMockCard({ m, onPress }: { m: WebMock; onPress: () => void }) {
  const a = m.attempt, s = a?.summary, live = !!a && a.resumable && !s;
  const state = !a ? "SHURU NAHI HUA" : s ? "RESULT" : live ? "CHAL RAHA HAI" : "RESULT AA RAHA HAI";
  const go = !a ? "Shuru karo" : live ? "Resume" : "Result dekho";
  const when = a?.submitted_at || a?.started_at || m.created_at;
  const size = [m.given != null ? `${m.given} sawaal` : "", m.minutes != null ? `${m.minutes} min` : ""].filter(Boolean).join(" · ");
  return <Press testID={`misfire-web-${m.set_id}`} onPress={onPress} scaleTo={0.99} accessibilityLabel={`${m.title}. ${go}`}>
    <DCard style={{ gap: space.sm }}>
      <T w="heavy" size={10} color={colors.custom_eyebrow} style={styles.caps}>{when ? `${unixDate(when)} · ${state}` : state}</T>
      <View style={styles.top}>
        <View style={{ flex: 1, gap: 2 }}>
          <T testID={`misfire-web-title-${m.set_id}`} w="heavy" size={16} numberOfLines={2}>{m.title}</T>
          {size ? <T testID={`misfire-web-size-${m.set_id}`} size={12} color={colors.muted}>{size}</T> : null}
        </View>
        {s ? <T testID={`misfire-web-score-${m.set_id}`} w="mono" size={15}>{s.score}<T w="monoRegular" size={12} color={colors.muted}>/{s.maximum}</T></T> : null}
      </View>
      <View style={styles.bottom}>
        {s ? <View style={styles.tags}>
          <ToneTag label={`${s.correct || 0} sahi`} tone={s.correct ? "good" : "mute"} icon="check" />
          <ToneTag label={`${s.incorrect || 0} galat`} tone={s.incorrect ? "bad" : "mute"} icon="close" />
          <ToneTag label={`${s.skipped || 0} chhode`} tone={s.skipped ? "warn" : "mute"} icon="minus" />
        </View> : <View />}
        <View style={styles.go}><T w="heavy" size={12.5} color={colors.brandText}>{go}</T><Icon name="arrow-right" size={15} color={colors.brandText} /></View>
      </View>
    </DCard>
  </Press>;
}

export function WebMocksTab({ uid }: { uid: string }) {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const list = usePaged<WebMock>(webMocksKey(uid), loadWebMocks);
  // Back from a paper (started, handed in, its time over) or from the website: the cards say where each mock is now.
  useListFocus(list.revalidate);
  return <FlatList testID="misfire-web-mocks" data={list.items} keyExtractor={(m) => m.set_id} initialNumToRender={8} windowSize={7}
    contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: insets.bottom + space.xxl, gap: space.md }}
    refreshControl={<RefreshControl refreshing={false} onRefresh={list.reload} />}
    ListHeaderComponent={<View style={{ gap: space.md }}>
      <ChoiceHero testID="misfire-web-hero">
        <T w="heavy" size={11} color={ON_HERO.soft} style={heroStyles.kicker}>MISFIRE MOCK</T>
        <T w="heavy" size={21} color={ON_HERO.ink}>Galtiyon se JEE Main mock</T>
        <T size={13} color={ON_HERO.soft}>Paper jeelive.ai par banega: timer, autosave, result aur Analysis har paper ki tarah. App aur website, dono par chalega. Jo sahi karoge, woh “Samajh gaya” ho jayenge.</T>
        <Pill testID="misfire-web-new" icon="fire" label="Naya mock banao" bg={colors.custom_card} ink={colors.custom_chipBloodDeep}
          onPress={() => router.push({ pathname: "/misfire/mock/new", params: { web: "1" } } as any)} />
      </ChoiceHero>
      <ErrorBox error={list.error && !list.first ? "Mocks ki list abhi nahi aa paayi. Thodi der mein dobara try karo." : ""} retry={list.reload} testID="misfire-web-error" />
    </View>}
    renderItem={({ item }) => <WebMockCard m={item} onPress={() => router.push(webMockPath(item) as any)} />}
    ListEmptyComponent={list.loading && !list.first ? <View testID="misfire-web-loading" style={{ gap: space.md }}><Skeleton h={120} /><Skeleton h={120} /></View>
      : list.first ? <DCard testID="misfire-web-empty"><Empty icon="fire" title="Abhi koi Misfire Mock nahi bana." body="Pehla mock banao. Woh yahan, My Tests mein aur jeelive.ai par, teeno jagah dikhega." /></DCard> : undefined}
    ListFooterComponent={<View style={{ gap: space.sm }}>
      <ErrorBox error={list.moreError ? "Aur mocks abhi nahi aa paaye. Dobara try karo." : ""} testID="misfire-web-more-error" />
      {list.hasMore ? <Pill testID="misfire-web-more" kind="outline" label="Aur mocks dikhao" busy={list.busy} onPress={list.more} /> : null}
    </View>} />;
}

const styles = StyleSheet.create({
  caps: { letterSpacing: 1.4 },
  top: { flexDirection: "row", alignItems: "flex-start", gap: space.md },
  bottom: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: space.sm },
  tags: { flexDirection: "row", alignItems: "center", gap: 6, flexWrap: "wrap" },
  go: { minHeight: 32, flexDirection: "row", alignItems: "center", gap: 4 },
});
