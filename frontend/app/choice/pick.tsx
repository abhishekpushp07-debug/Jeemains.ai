// Student Choice, step 1 of 2: the chapters (the JEE Main chapter-wise ones). A subject at a time (Physics, Chemistry,
// Maths), or by name: the search box looks in all three subjects at once (src/choice/search.ts). Chapters can be ticked
// in one, two or all three. Step 2 is the ticked chapters' whole tests, or, once the website can make a paper of chosen
// questions (bank.pick), the questions of those chapters.
import React, { useEffect, useMemo, useRef, useState } from "react";
import { FlatList, StyleSheet, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { Empty, ErrorBox, Icon, Press, Skeleton, T } from "@/src/components/ui";
import { Pill, ScreenHeader } from "@/src/components/design";
import { ScreenMotion } from "@/src/motion";
import { colors, fonts, noOutline, radius, space, subjectColor } from "@/src/theme";
import { Chapter, SHORT, Subject } from "@/src/choice/api";
import { SubjectTabs, subjectWash } from "@/src/choice/looks";
import { StepBar, Tick, useBank } from "@/src/choice/parts";
import { Found, findChapters, searchIndex } from "@/src/choice/search";
import { chosenChapters, hasChapter, pickedCount, pickedIn, toggleChapter, useChoice } from "@/src/choice/store";

/** `subject` = said on the row (a search result can be of any subject); `tone` = the row's own subject, whose colour a chosen row wears. */
function ChapterRow({ c, on, picked, subject, tone }: { c: Chapter; on: boolean; picked: number; subject?: Subject; tone: Subject }) {
  return <Press testID={`choice-chapter-${c.id}`} onPress={() => toggleChapter(c.id)} scaleTo={0.99} accessibilityRole="checkbox" accessibilityState={{ checked: on }}
    accessibilityLabel={`${c.title}${subject ? `, ${SHORT[subject]}` : ""}, ${c.count} sawaal${on ? ", chuna hua" : ""}`} style={[styles.row, on && { borderColor: subjectColor(tone), backgroundColor: subjectWash(tone) }]}>
    <Tick on={on} color={subjectColor(tone)} />
    <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
      <T testID={`choice-chapter-${c.id}-title`} w="heavy" size={15} numberOfLines={2}>{c.n ? `${c.n}. ` : ""}{c.title}</T>
      <T size={12} color={colors.muted} numberOfLines={1}>{subject ? <T testID={`choice-chapter-${c.id}-subject`} w="heavy" size={12} color={subjectColor(subject)}>{SHORT[subject]} · </T> : null}
        {c.count} sawaal{c.mcq || c.integer ? ` · ${c.mcq} MCQ · ${c.integer} numerical` : ""}</T>
    </View>
    {picked ? <View testID={`choice-chapter-${c.id}-picked`} style={styles.picked}><T w="heavy" size={11.5} color={colors.onSurfaceInverse}>{picked} chune</T></View> : null}
  </Press>;
}

export default function ChooseChapters() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const res = useBank(user?.id);
  useChoice(user?.id);
  const bank = res.data?.ready ? res.data : null;
  const [subject, setSubject] = useState<Subject | "">("");
  const [q, setQ] = useState("");
  const list = useRef<FlatList<Found>>(null);
  const current = bank?.subjects.find(s => s.name === subject) || bank?.subjects[0];
  // A name typed in the search box: the chapters of all three subjects that fit it, instead of one subject's list.
  const index = useMemo(() => searchIndex(bank?.subjects || []), [bank]);
  const found = useMemo(() => (q.trim() ? findChapters(index, q) : null), [index, q]);
  const rows = useMemo(() => found?.items || (current ? current.chapters.map(c => ({ c, subject: current.name })) : []), [found, current]);
  useEffect(() => { list.current?.scrollToOffset({ offset: 0, animated: false }); }, [q]); // a new list starts at its top
  const chosen = chosenChapters(), questions = pickedCount();
  // Only chapters the bank still has count (one may have gone since it was ticked).
  const live = useMemo(() => new Set(bank?.subjects.flatMap(s => s.chapters.map(c => c.id))), [bank]);
  const ticked = chosen.filter(id => live.has(id)).length;
  const sum = useMemo(() => (bank?.subjects || []).flatMap(s => s.chapters).filter(c => chosen.includes(c.id)).reduce((n, c) => n + c.count, 0), [bank, chosen]);
  return <ScreenMotion>
    <View testID="choice-pick-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <ScreenHeader testID="choice-pick-header" title="Chapters chuno" eyebrow="Student Choice · Step 1 of 2" backTestID="choice-pick-back"
        onBack={() => (router.canGoBack() ? router.back() : router.replace("/choice"))} />
      {bank ? <View style={styles.searchWrap}>
        <View testID="choice-search" style={styles.search}>
          <Icon name="magnify" size={20} color={colors.muted} />
          <TextInput testID="choice-search-input" value={q} onChangeText={setQ} placeholder="Chapter ka naam likho…" placeholderTextColor={colors.muted} maxLength={60}
            autoCorrect={false} autoCapitalize="none" returnKeyType="search" accessibilityLabel="Chapter ka naam likh kar dhoondo" style={[styles.searchInput, noOutline]} />
          {q ? <Press testID="choice-search-clear" onPress={() => setQ("")} accessibilityLabel="Search hatao" style={styles.clear}><Icon name="close-circle" size={18} color={colors.muted} /></Press> : null}
        </View>
      </View> : null}
      {/* A tap on a chapter ticks it with the keyboard still open; dragging the list puts the keyboard away. */}
      <FlatList ref={list} testID="choice-chapter-list" data={rows} keyExtractor={r => r.c.id} extraData={[chosen, questions]}
        renderItem={({ item }) => <ChapterRow c={item.c} on={hasChapter(item.c.id)} picked={pickedIn(item.c.id)} subject={found ? item.subject : undefined} tone={item.subject} />}
        keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag"
        showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: space.xl, gap: space.sm }}
        ListHeaderComponent={<View style={{ gap: space.md, paddingBottom: space.xs }}>
          <ErrorBox testID="choice-pick-error" error={res.error} retry={res.reload} />
          {!res.data && !res.error ? <View testID="choice-pick-loading" style={{ gap: space.sm }}><Skeleton h={44} /><Skeleton h={64} /><Skeleton h={64} /><Skeleton h={64} /></View> : null}
          {found ? (found.items.length
            ? <T testID="choice-search-count" w="bold" size={12.5} color={colors.custom_softText}>{found.close ? "Is naam ka chapter nahi mila. Milte-julte naam:" : `${found.items.length} chapter${found.items.length === 1 ? "" : "s"} mile · teeno subjects mein dhoonda`}</T>
            : <Empty testID="choice-search-none" icon="magnify" title="Is naam ka chapter nahi mila" body="Spelling dekh lo, ya subject se chapter chuno."
              action={<Pill testID="choice-search-reset" kind="outline" label="Search hatao" onPress={() => setQ("")} />} />)
            : bank && current ? <>
              <SubjectTabs prefix="choice-subject" value={current.name} onChange={setSubject}
                items={bank.subjects.map(s => ({ subject: s.name, count: s.chapters.filter(c => hasChapter(c.id)).length }))} />
              <T testID="choice-pick-hint" size={12.5} color={colors.muted}>Jitne chahiye utne chapter tick karo, kisi bhi subject se. {bank.pick ? "Sawaal agle step mein chunoge." : "Agle step mein har chune chapter ka poora test milega."}</T>
            </> : null}
          {res.data && !bank ? <Empty testID="choice-pick-not-ready" icon="database-search-outline" title="Chapters abhi nahi mile" body="Thodi der mein dobara dekho." /> : null}
        </View>} />
      {bank ? <StepBar testID="choice-pick-bar" big={ticked ? `${ticked} chapter${ticked === 1 ? "" : "s"} chune` : "Chapter chuno"}
        small={!ticked ? "Kam se kam ek chapter tick karo" : bank.pick ? (questions ? `${questions} sawaal chune hue hain` : "Ab inke sawaal chuno") : `${ticked} test${ticked === 1 ? "" : "s"} · ${sum} sawaal`}
        label={bank.pick ? "Sawaal chuno" : "Tests dekho"} disabled={!ticked} onPress={() => router.push(bank.pick ? "/choice/questions" : "/choice/tests")} /> : null}
    </View>
  </ScreenMotion>;
}

const styles = StyleSheet.create({
  searchWrap: { paddingHorizontal: space.lg, paddingBottom: space.md },
  search: { flexDirection: "row", alignItems: "center", height: 48, paddingHorizontal: space.lg, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card },
  searchInput: { flex: 1, alignSelf: "stretch", fontFamily: fonts.medium, fontSize: 14, color: colors.onSurface, paddingHorizontal: space.sm, paddingVertical: 0 },
  clear: { width: 44, height: 44, alignItems: "center", justifyContent: "center", marginRight: -space.md },
  row: { flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 64, paddingVertical: 10, paddingHorizontal: 14, borderRadius: 18, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card },
  picked: { height: 24, paddingHorizontal: 9, borderRadius: 12, justifyContent: "center", backgroundColor: colors.onSurface },
});
