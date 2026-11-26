// Student Choice, step 2 of 2 while the website cannot make a paper of chosen questions yet: the ticked chapters' whole
// tests (the JEE Main chapter-wise tests the website already has), to be taken one after another. Each row says where
// the student stands with that test (their own attempt, read from the chapter-wise list) and opens it: the test's page,
// the attempt in progress, or its result. From there it is an ordinary paper.
import React, { memo, useMemo } from "react";
import { FlatList, StyleSheet, View } from "react-native";
import { Redirect, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { useListFocus } from "@/src/useListFocus";
import { ErrorBox, Press, Skeleton, T } from "@/src/components/ui";
import { DCard, Pill, ScreenHeader, StatusLine } from "@/src/components/design";
import { ScreenMotion } from "@/src/motion";
import { colors, radius, space, subjectColor } from "@/src/theme";
import { Attempt, Chapter, ChapterTest, SHORT, Subject, TestPage, getAttempts } from "@/src/choice/api";
import { useBank } from "@/src/choice/parts";
import { ChoiceHero, ON_HERO, heroStyles, subjectWash } from "@/src/choice/looks";
import { choiceLoaded, chosenChapters, useChoice } from "@/src/choice/store";
import { attemptAction } from "@/app/catalogue";

type Mine = Chapter & { subject: Subject; test: ChapterTest };

/** One chapter's test. `attempt`: undefined = the student's attempts are not read yet (the row cannot be opened: a test
 *  in progress must be resumed, never started a second time); `wait` = they are being read right now. */
const TestRow = memo(function TestRow({ c, attempt, head, wait }: { c: Mine; attempt: Attempt | null | undefined; head: boolean; wait: boolean }) {
  const router = useRouter();
  const act = attempt === undefined ? null : attemptAction({ id: c.id, attempt });
  const status = act?.label === "Resume" ? (["In progress", colors.custom_timerAmber] as const) : act?.label === "Result" ? (["Completed", colors.custom_mint] as const) : null;
  // Start in the app's red, Resume in My Tests' yellow (In progress), Result in its baby pink (Completed); anything else plain.
  const badge = act?.label === "Start" ? [colors.brandPrimary, colors.onBrandPrimary] : act?.label === "Resume" ? [colors.custom_tabSun, colors.custom_tabInk]
    : act?.label === "Result" ? [colors.custom_tabPink, colors.custom_tabInk] : [colors.custom_cardRaised, colors.onSurface];
  const id = `choice-test-${c.id}`;
  return <View style={{ gap: space.sm }}>
    {head ? <T testID={`choice-tests-subject-${c.subject.toLowerCase()}`} w="heavy" size={11} color={subjectColor(c.subject)} style={styles.subject}>{SHORT[c.subject].toUpperCase()}</T> : null}
    <Press testID={id} disabled={!act} onPress={() => act && router.push(act.to as any)} scaleTo={0.985} accessibilityLabel={`${c.title}. ${act?.label ?? "Loading"}`}>
      <DCard style={styles.row}>
        <View style={[styles.number, { backgroundColor: subjectWash(c.subject), borderColor: subjectColor(c.subject) }]}><T w="heavy" size={15} color={subjectColor(c.subject)}>{c.n ?? "•"}</T></View>
        <View style={{ flex: 1, minWidth: 0, gap: 3 }}>
          <T testID={`${id}-title`} w="heavy" size={15} numberOfLines={3}>{c.title}</T>
          <T testID={`${id}-facts`} size={11.5} color={colors.muted}>{c.count} Q · {c.test.minutes ? `${c.test.minutes} min` : "Untimed"} · +{c.test.correct}/{c.test.wrong} · {c.test.marks} marks</T>
          {status ? <StatusLine testID={`${id}-status`} label={status[0]} color={status[1]} /> : null}
        </View>
        {act ? <View testID={`${id}-action`} style={[styles.action, { backgroundColor: badge[0] }]}>
          <T w="heavy" size={12} color={badge[1]}>{act.label}</T>
        </View> : wait ? <Skeleton h={36} style={{ width: 64, borderRadius: radius.pill }} /> : null}
      </DCard>
    </Press>
  </View>;
});

export default function ChapterTests() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const res = useBank(user?.id);
  const version = useChoice(user?.id);
  const bank = res.data?.ready ? res.data : null;
  // The ticked chapters that have a test, in the bank's own order, each with its subject.
  const mine = useMemo(() => {
    const ticked = new Set(chosenChapters());
    return (bank?.subjects || []).flatMap(s => s.chapters.flatMap(c => (ticked.has(c.id) && c.test ? [{ ...c, subject: s.name, test: c.test }] : [])));
  }, [bank, version]) as Mine[]; // eslint-disable-line react-hooks/exhaustive-deps
  // The pages of the chapter-wise list those tests are on: the student's attempts are read from them.
  const pages = useMemo(() => {
    const seen = new Map<string, TestPage>();
    mine.forEach(c => seen.set(`${c.subject[0]}${c.test.page}`, { subject: c.subject, page: c.test.page }));
    return [...seen.entries()].sort(([a], [b]) => (a < b ? -1 : 1));
  }, [mine]);
  const attempts = useCached<Record<string, Attempt | null>>(user && pages.length ? `u.${user.id}.choice.attempts.${pages.map(([k]) => k).join("")}` : null, getAttempts(pages.map(([, p]) => p)), false);
  useListFocus(attempts.revalidate);
  const mineOf = (c: Mine) => (attempts.data ? attempts.data[c.id] ?? null : undefined);
  const labels = attempts.data ? mine.map(c => attemptAction({ id: c.id, attempt: attempts.data![c.id] }).label) : null;
  const done = labels ? labels.filter(l => l === "Result").length : 0;
  const running = labels ? labels.filter(l => l === "Resume").length : 0;

  // Opened without a ticked chapter (a refreshed page): back to step 1.
  if (res.data && choiceLoaded() && (!bank || !mine.length)) return <Redirect href={bank ? "/choice/pick" : "/choice"} />;
  return <ScreenMotion>
    <View testID="choice-tests-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <ScreenHeader testID="choice-tests-header" title="Aapke chapter tests" eyebrow="Student Choice · Step 2 of 2" backTestID="choice-tests-back"
        onBack={() => (router.canGoBack() ? router.back() : router.replace("/choice/pick"))} />
      <FlatList testID="choice-tests-list" data={mine} keyExtractor={c => c.id} extraData={[attempts.data, attempts.error]}
        renderItem={({ item, index }) => <TestRow c={item} attempt={mineOf(item)} wait={!attempts.error} head={index === 0 || mine[index - 1].subject !== item.subject} />}
        refreshing={attempts.refreshing} onRefresh={attempts.reload} showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: insets.bottom + space.xl, gap: space.md }}
        ListHeaderComponent={<View style={{ gap: space.md }}>
          <ErrorBox testID="choice-tests-bank-error" error={res.error} retry={res.reload} />
          {mine.length ? <View style={{ gap: space.md }}>
            <ChoiceHero testID="choice-tests-hero">
              <T w="heavy" size={10.5} color={ON_HERO.soft} style={heroStyles.kicker}>STUDENT CHOICE · AAPKE CHAPTER TESTS</T>
              <T testID="choice-tests-count" w="heavy" size={19} color={ON_HERO.ink}>{mine.length} chapter test{mine.length === 1 ? "" : "s"}{attempts.data ? ` · ${done} ho gaye` : ""}</T>
              <View style={heroStyles.counts}>
                {([["done", "Ho gaye", done], ["running", "Chal rahe", running], ["left", "Baaki", mine.length - done - running]] as const).map(([k, label, value], i) =>
                  <View key={k} style={[heroStyles.count, i > 0 && heroStyles.countLine]}>
                    <T testID={`choice-tests-${k}`} w="mono" size={20} color={ON_HERO.ink}>{labels ? value : "–"}</T>
                    <T w="bold" size={10.5} color={ON_HERO.soft} numberOfLines={1}>{label}</T>
                  </View>)}
              </View>
            </ChoiceHero>
            <T testID="choice-tests-hint" size={12.5} color={colors.muted} style={{ lineHeight: 18 }}>Har chapter ka poora test hai: jo chaho pehle do, ek-ek karke. Result, analysis aur solutions har paper ki tarah milte hain.</T>
          </View> : !res.data && !res.error ? <View testID="choice-tests-loading" style={{ gap: space.md }}><Skeleton h={76} /><Skeleton h={76} /><Skeleton h={76} /></View> : null}
          <ErrorBox testID="choice-tests-error" error={attempts.error} retry={attempts.reload} />
        </View>}
        ListFooterComponent={mine.length ? <Pill testID="choice-tests-change" kind="outline" icon="format-list-checks" label="Chapters badlo" style={{ marginTop: space.sm }}
          onPress={() => router.dismissTo("/choice/pick")} /> : undefined} />
    </View>
  </ScreenMotion>;
}

const styles = StyleSheet.create({
  subject: { letterSpacing: 1.6, marginTop: space.xs },
  row: { flexDirection: "row", gap: space.md, alignItems: "center", padding: space.md, paddingRight: space.lg },
  number: { width: 46, height: 46, borderRadius: 23, borderWidth: 1, alignItems: "center", justifyContent: "center" },
  action: { paddingHorizontal: 14, height: 36, borderRadius: radius.pill, alignItems: "center", justifyContent: "center" },
});
