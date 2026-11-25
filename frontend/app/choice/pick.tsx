// Student Choice, step 1 of 2: the chapters. A subject at a time (Physics, Chemistry, Maths); chapters can be ticked in
// one, two or all three. The questions of the ticked chapters are chosen on the next screen.
import React, { useMemo, useState } from "react";
import { FlatList, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { Empty, ErrorBox, Press, Skeleton, T } from "@/src/components/ui";
import { ScreenHeader } from "@/src/components/design";
import { ScreenMotion } from "@/src/motion";
import { PillRow } from "@/src/misfire/parts";
import { colors, space } from "@/src/theme";
import { Chapter, SHORT, Subject } from "@/src/choice/api";
import { StepBar, Tick, useBank } from "@/src/choice/parts";
import { chosenChapters, hasChapter, pickedCount, pickedIn, toggleChapter, useChoice } from "@/src/choice/store";

function ChapterRow({ c, on, picked }: { c: Chapter; on: boolean; picked: number }) {
  return <Press testID={`choice-chapter-${c.id}`} onPress={() => toggleChapter(c.id)} scaleTo={0.99} accessibilityRole="checkbox" accessibilityState={{ checked: on }}
    accessibilityLabel={`${c.title}, ${c.count} sawaal${on ? ", chuna hua" : ""}`} style={[styles.row, on && styles.rowOn]}>
    <Tick on={on} />
    <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
      <T testID={`choice-chapter-${c.id}-title`} w="heavy" size={15} numberOfLines={2}>{c.n ? `${c.n}. ` : ""}{c.title}</T>
      <T size={12} color={colors.muted} numberOfLines={1}>{c.count} sawaal{c.mcq || c.integer ? ` · ${c.mcq} MCQ · ${c.integer} numerical` : ""}</T>
    </View>
    {picked ? <View testID={`choice-chapter-${c.id}-picked`} style={styles.picked}><T w="heavy" size={11.5} color={colors.onSurfaceInverse}>{picked} chune</T></View> : null}
  </Press>;
}

export default function ChooseChapters() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const res = useBank(user?.id);
  useChoice();
  const bank = res.data?.ready ? res.data : null;
  const [subject, setSubject] = useState<Subject | "">("");
  const current = bank?.subjects.find(s => s.name === subject) || bank?.subjects[0];
  const chosen = chosenChapters(), questions = pickedCount();
  // Only chapters the bank still has count (one may have gone since it was ticked).
  const live = useMemo(() => new Set(bank?.subjects.flatMap(s => s.chapters.map(c => c.id))), [bank]);
  const ticked = chosen.filter(id => live.has(id)).length;
  return <ScreenMotion>
    <View testID="choice-pick-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <ScreenHeader testID="choice-pick-header" title="Chapters chuno" eyebrow="Student Choice · Step 1 of 2" backTestID="choice-pick-back"
        onBack={() => (router.canGoBack() ? router.back() : router.replace("/choice"))} />
      <FlatList testID="choice-chapter-list" data={current?.chapters || []} keyExtractor={c => c.id} extraData={[chosen, questions]}
        renderItem={({ item }) => <ChapterRow c={item} on={hasChapter(item.id)} picked={pickedIn(item.id)} />}
        showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: space.xl, gap: space.sm }}
        ListHeaderComponent={<View style={{ gap: space.md, paddingBottom: space.xs }}>
          <ErrorBox testID="choice-pick-error" error={res.error} retry={res.reload} />
          {!res.data && !res.error ? <View testID="choice-pick-loading" style={{ gap: space.sm }}><Skeleton h={44} /><Skeleton h={64} /><Skeleton h={64} /><Skeleton h={64} /></View> : null}
          {bank && current ? <>
            <PillRow prefix="choice-subject" value={current.name} onChange={k => setSubject(k as Subject)}
              items={bank.subjects.map(s => ({ key: s.name, label: SHORT[s.name], count: s.chapters.filter(c => hasChapter(c.id)).length }))} />
            <T testID="choice-pick-hint" size={12.5} color={colors.muted}>Jitne chahiye utne chapter tick karo, kisi bhi subject se. Sawaal agle step mein chunoge.</T>
          </> : null}
          {res.data && !bank ? <Empty testID="choice-pick-not-ready" icon="database-search-outline" title="Sawaalon ka bank jud raha hai" body="Thodi der mein dobara dekho." /> : null}
        </View>} />
      {bank ? <StepBar testID="choice-pick-bar" big={ticked ? `${ticked} chapter${ticked === 1 ? "" : "s"} chune` : "Chapter chuno"}
        small={questions ? `${questions} sawaal chune hue hain` : "Kam se kam ek chapter tick karo"} label="Sawaal chuno" disabled={!ticked} onPress={() => router.push("/choice/questions")} /> : null}
    </View>
  </ScreenMotion>;
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 64, paddingVertical: 10, paddingHorizontal: 14, borderRadius: 18, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card },
  rowOn: { borderColor: colors.onSurface },
  picked: { height: 24, paddingHorizontal: 9, borderRadius: 12, justifyContent: "center", backgroundColor: colors.onSurface },
});
