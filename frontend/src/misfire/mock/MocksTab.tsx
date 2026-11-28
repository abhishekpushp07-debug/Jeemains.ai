// Misfire's "Offline Misfire" tab (also behind the offline door, app/offline/misfire): make a new one, and every mock
// made on this phone (newest first) with its result.
import React from "react";
import { FlatList, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Empty, Icon, Press, T } from "@/src/components/ui";
import { DCard, Pill } from "@/src/components/design";
import { ToneTag } from "@/src/analysis/parts";
import { colors, space } from "@/src/theme";
import { unixDate } from "@/src/navigation";
import { timeLabel } from "@/src/choice/api";
import { ChoiceHero, ON_HERO, heroStyles } from "@/src/choice/looks";
import { useSendWaiting } from "./marking";
import { useMockPaths } from "./offline";
import { MockRow, mockOver, useMocks } from "./store";

function MockItem({ m, onPress }: { m: MockRow; onPress: () => void }) {
  const over = mockOver(m);
  const state = m.status === "done" ? "RESULT" : over ? "TIME OVER" : m.status === "active" ? "CHAL RAHA HAI" : "SHURU NAHI HUA";
  return <Press testID={`misfire-mock-${m.id}`} onPress={onPress} scaleTo={0.99} accessibilityLabel={`${m.title}. ${over ? "Result dekho" : m.status === "active" ? "Wapas jao" : "Shuru karo"}`}>
    <DCard style={{ gap: space.sm }}>
      <T w="heavy" size={10} color={colors.custom_eyebrow} style={styles.caps}>{`${unixDate(Math.round((m.started_at || m.made_at) / 1000))} · ${state}`}</T>
      <View style={styles.top}>
        <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
          <T testID={`misfire-mock-title-${m.id}`} w="heavy" size={16} numberOfLines={1}>{m.title}</T>
          <T size={12} color={colors.muted}>{m.count} sawaal · {timeLabel(m.minutes)}</T>
        </View>
        {m.score != null ? <T testID={`misfire-mock-score-${m.id}`} w="mono" size={15}>{m.score}<T w="monoRegular" size={12} color={colors.muted}>/{m.maximum}</T></T> : null}
      </View>
      <View style={styles.bottom}>
        {m.score != null ? <View style={styles.tags}>
          <ToneTag label={`${m.correct} sahi`} tone={m.correct ? "good" : "mute"} icon="check" />
          <ToneTag label={`${m.incorrect} galat`} tone={m.incorrect ? "bad" : "mute"} icon="close" />
          <ToneTag label={`${m.skipped} chhode`} tone={m.skipped ? "warn" : "mute"} icon="minus" />
        </View> : <View />}
        <View style={styles.go}><T w="heavy" size={12.5} color={colors.brandText}>{over ? "Result dekho" : m.status === "active" ? "Resume" : "Shuru karo"}</T><Icon name="arrow-right" size={15} color={colors.brandText} /></View>
      </View>
    </DCard>
  </Press>;
}

/** `online`: signed in (right answers still waiting are sent from here); behind the offline door they wait. */
export function MocksTab({ online = true }: { online?: boolean }) {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const mocks = useMocks();
  const paths = useMockPaths();
  useSendWaiting(mocks, online);
  return <FlatList testID="misfire-mocks" data={mocks} keyExtractor={(m) => m.id} initialNumToRender={8}
    contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: insets.bottom + space.xxl, gap: space.md }}
    ListHeaderComponent={<ChoiceHero testID="misfire-mock-hero">
      <T w="heavy" size={11} color={ON_HERO.soft} style={heroStyles.kicker}>OFFLINE MISFIRE</T>
      <T w="heavy" size={21} color={ON_HERO.ink}>Galtiyon se JEE Main mock</T>
      <T size={13} color={ON_HERO.soft}>Subject, chapter aur ginti chuno. Internet na ho tab bhi chalega: sawaal phone par rakhe papers se. Jo sahi karoge, woh “Samajh gaya” ho jayenge.</T>
      <Pill testID="misfire-mock-new" icon="fire" label="Naya mock banao" bg={colors.custom_card} ink={colors.custom_chipBloodDeep} onPress={() => router.push(paths.make)} />
    </ChoiceHero>}
    renderItem={({ item }) => <MockItem m={item} onPress={() => router.push(paths.one(item.id))} />}
    ListEmptyComponent={<DCard testID="misfire-mocks-empty"><Empty icon="fire" title="Abhi koi mock nahi bana." body="Pehla mock banao. Woh yahan aur My Tests, dono mein dikhega." /></DCard>} />;
}

const styles = StyleSheet.create({
  caps: { letterSpacing: 1.4 },
  top: { flexDirection: "row", alignItems: "flex-start", gap: space.md },
  bottom: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: space.sm },
  tags: { flexDirection: "row", alignItems: "center", gap: 6, flexWrap: "wrap" },
  go: { minHeight: 32, flexDirection: "row", alignItems: "center", gap: 4 },
});
