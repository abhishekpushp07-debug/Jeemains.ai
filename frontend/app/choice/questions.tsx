// Student Choice, step 2 of 2: the questions. The ticked chapters, subject by subject and chapter by chapter; a chapter's
// questions are listed WITHOUT options (those come in the paper) and a tap ticks one. The bar at the bottom says how big
// the paper is and how much time it gets; "Paper banao" asks jeelive.ai to make it, and its page opens.
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { FlatList, View, useWindowDimensions } from "react-native";
import { Redirect, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { uuid } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { Empty, ErrorBox, Notice, Skeleton, T, buzz } from "@/src/components/ui";
import { DSheet, Pill, ScreenHeader } from "@/src/components/design";
import { ScreenMotion } from "@/src/motion";
import { PillRow } from "@/src/misfire/parts";
import { colors, space } from "@/src/theme";
import { ChapterQuestions, Question, SHORT, Subject, getChapter, makePaper, minutesFor, timeLabel, totalOf } from "@/src/choice/api";
import { Makeup, QuestionCard, StepBar, stemWidth, useBank } from "@/src/choice/parts";
import { SubjectTabs } from "@/src/choice/looks";
import { choiceLoaded, chosenChapters, clearChoice, counts, hasQuestion, orderedIds, pickedCount, pickedIn, toggleQuestion, useChoice } from "@/src/choice/store";

export default function ChooseQuestions() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const res = useBank(user?.id);
  const version = useChoice(user?.id);
  const bank = res.data?.ready ? res.data : null;
  const width = stemWidth(useWindowDimensions().width);
  // The ticked chapters, in the bank's own order, each with its subject.
  const mine = useMemo(() => {
    const ticked = new Set(chosenChapters());
    return (bank?.subjects || []).flatMap(s => s.chapters.filter(c => ticked.has(c.id)).map(c => ({ ...c, subject: s.name })));
  }, [bank, version]); // eslint-disable-line react-hooks/exhaustive-deps
  const subjects = useMemo(() => [...new Set(mine.map(c => c.subject))], [mine]);
  const [subject, setSubject] = useState<Subject | "">("");
  const [chapterId, setChapterId] = useState("");
  const inSubject = mine.filter(c => c.subject === (subjects.includes(subject as Subject) ? subject : subjects[0]));
  const chapter = inSubject.find(c => c.id === chapterId) || inSubject[0];
  // A chapter's questions are kept in memory while the app is open (their picture links do not live for ever).
  // (Asked only while questions can be chosen: otherwise this screen is about to hand over to the chapters' tests.)
  const list = useCached<ChapterQuestions>(chapter && user && bank?.pick ? `choice.chapter.${chapter.id}` : null, getChapter(user?.id || "", chapter?.id || ""), false);
  // No chapter yet (the ticks are still being read, or none is ticked): nothing to list. Without this check a page
  // opened straight on this address broke ("cannot read items of null").
  const rows = chapter && list.data?.id === chapter.id ? list.data.items : null;
  const top = useRef<React.ElementRef<typeof FlatList<Question>>>(null);
  useEffect(() => { top.current?.scrollToOffset({ offset: 0, animated: false }); }, [chapter?.id]);

  const [full, setFull] = useState("");
  useEffect(() => { if (!full) return; const t = setTimeout(() => setFull(""), 3200); return () => clearTimeout(t); }, [full]);
  const toggle = useCallback((q: Question) => {
    if (!bank || !chapter) return;
    const said = toggleQuestion(q.id, { chapter: chapter.id, subject: chapter.subject, n: q.n ?? 0 }, bank);
    if (said === "ok") { setFull(""); return; }
    buzz("warning");
    setFull(said === "full" ? `${bank.max_questions} sawaal ho gaye: ek paper mein isse zyada nahi. Koi hatao, tab naya chuno.`
      : `${SHORT[chapter.subject]} ke ${bank.max_per_subject} sawaal ho gaye. Koi hatao, tab naya chuno.`);
  }, [bank, chapter]);

  const [review, setReview] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const asked = useRef({ ids: "", key: "" });
  const n = pickedCount(), made = counts();
  async function make() {
    if (!bank || !n || busy) return;
    const ids = orderedIds(bank), joined = ids.join(",");
    if (asked.current.ids !== joined) asked.current = { ids: joined, key: uuid() }; // the same key for every retry of this one paper
    setBusy(true); setError("");
    try {
      const paper = await makePaper({ mode: "pick", question_ids: ids }, asked.current.key);
      setReview(false);
      clearChoice();
      router.dismissTo("/choice");
      router.push(`/set/${paper}`);
    } catch (e: any) {
      setError(e?.message || "Paper ban nahi paaya. Dobara try karo.");
      setBusy(false);
    }
  }

  // Opened without a ticked chapter (a refreshed page): back to step 1. While the website cannot make a paper of chosen
  // questions, step 2 is the chapters' own tests.
  if (res.data && choiceLoaded() && (!bank || !mine.length || !bank.pick) && !busy) return <Redirect href={!bank ? "/choice" : mine.length && !bank.pick ? "/choice/tests" : "/choice/pick"} />;
  const next = chapter ? mine[mine.findIndex(c => c.id === chapter.id) + 1] : undefined;
  return <ScreenMotion>
    <View testID="choice-questions-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <ScreenHeader testID="choice-questions-header" title="Sawaal chuno" eyebrow="Student Choice · Step 2 of 2" backTestID="choice-questions-back"
        onBack={() => (router.canGoBack() ? router.back() : router.replace("/choice/pick"))} />
      <FlatList ref={top} testID="choice-question-list" data={rows || []} keyExtractor={q => q.id} extraData={version}
        renderItem={({ item, index }) => <QuestionCard q={item} k={index} on={hasQuestion(item.id)} width={width} onToggle={toggle} />}
        // A typed question with maths holds a typesetter: only the few near the screen are kept drawn.
        initialNumToRender={6} maxToRenderPerBatch={6} windowSize={7} showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: space.xl, gap: space.sm }}
        ListHeaderComponent={<View style={{ gap: space.md, paddingBottom: space.xs }}>
          <ErrorBox testID="choice-questions-bank-error" error={res.error} retry={res.reload} />
          {chapter ? <>
            {subjects.length > 1 ? <SubjectTabs prefix="choice-q-subject" value={chapter.subject} onChange={s => { setSubject(s); setChapterId(""); }}
              items={subjects.map(s => ({ subject: s, count: made[s] }))} /> : null}
            {inSubject.length > 1 ? <PillRow prefix="choice-q-chapter" value={chapter.id} onChange={setChapterId}
              items={inSubject.map(c => ({ key: c.id, label: c.title, count: pickedIn(c.id) }))} /> : null}
            <View style={{ gap: 2 }}>
              <T testID="choice-questions-chapter" w="heavy" size={18}>{chapter.title}</T>
              <T testID="choice-questions-hint" size={12.5} color={colors.muted}>{SHORT[chapter.subject]} · {rows ? rows.length : chapter.count} sawaal · yahan sirf sawaal hain, options paper mein milenge</T>
            </View>
          </> : null}
          <ErrorBox testID="choice-questions-error" error={list.error} retry={list.reload} />
          {chapter && !rows && !list.error ? <View testID="choice-questions-loading" style={{ gap: space.sm }}><Skeleton h={96} /><Skeleton h={96} /><Skeleton h={96} /></View> : null}
        </View>}
        ListEmptyComponent={rows ? <Empty testID="choice-questions-empty" icon="book-open-page-variant-outline" title="Is chapter mein sawaal nahi mile" body="Doosra chapter chuno." /> : undefined}
        ListFooterComponent={rows?.length && next ? <Pill testID="choice-next-chapter" kind="outline" label={`Agla chapter: ${next.title}`} iconRight="arrow-right" style={{ marginTop: space.sm }}
          onPress={() => { setSubject(next.subject); setChapterId(next.id); }} /> : undefined} />
      {full ? <View style={{ paddingHorizontal: space.lg, paddingBottom: space.sm }}><Notice testID="choice-full" tone="warning">{full}</Notice></View> : null}
      {bank ? <StepBar testID="choice-questions-bar" big={`${n} / ${bank.max_questions} sawaal`}
        small={n ? `${timeLabel(minutesFor(made, bank.minutes))} · ${n * bank.marks.correct} marks` : "Sawaal par tap karke chuno"} label="Paper banao" disabled={!n} onPress={() => { setError(""); setReview(true); }} /> : null}
      {bank ? <DSheet testID="choice-review-sheet" visible={review} onClose={() => { if (!busy) setReview(false); }} title="Aapka paper">
        <Makeup testID="choice-review-makeup" counts={made} bank={bank} />
        <T testID="choice-review-rule" size={13} color={colors.custom_softText} style={{ lineHeight: 20 }}>
          Poore {totalOf(made) * bank.marks.correct} marks. Sahi jawab +{bank.marks.correct}, galat {bank.marks.wrong}, chhoda hua 0. Paper Physics, Chemistry, Maths ke order mein banega; result, analysis aur solutions har paper ki tarah milenge.
        </T>
        {error ? <Notice testID="choice-review-error" tone="error">{error}</Notice> : null}
        <Pill testID="choice-make" size="lg" icon="check" label="Haan, paper banao" busy={busy} onPress={make} />
        <Pill testID="choice-review-back" kind="outline" label="Aur sawaal chuno" disabled={busy} onPress={() => setReview(false)} />
      </DSheet> : null}
    </View>
  </ScreenMotion>;
}
