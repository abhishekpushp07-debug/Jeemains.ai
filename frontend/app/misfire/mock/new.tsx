// Misfire Mock, the choosing step: subject by subject, how many questions (up to 25, JEE Main's count) and from which
// chapters of the student's own open Misfire. The questions themselves are not shown. "Mock banao" draws them and opens
// the mock; its clock starts only on "Shuru karo" there.
import React, { useEffect, useRef, useState } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { Empty, ErrorBox, Icon, Press, Skeleton, T } from "@/src/components/ui";
import { DCard, DSheet, Pill, ScreenHeader } from "@/src/components/design";
import { RedTabs } from "@/src/components/RedTabs";
import { ScreenMotion } from "@/src/motion";
import { colors, radius, space } from "@/src/theme";
import { Counts, NONE, SHORT, SUBJECTS, Subject, minutesFor, timeLabel, totalOf } from "@/src/choice/api";
import { ChoiceHero, ON_HERO, SubjectTabs, heroStyles } from "@/src/choice/looks";
import { StepBar, Tick } from "@/src/choice/parts";
import { getPage, misfireKey } from "@/src/misfire/api";
import { chapterLabel, chapterName } from "@/src/misfire/parts";
import { misfireAccount } from "@/src/misfire/store";
import { MARKS } from "@/src/misfire/mock/store";
import { MAX_PER_SUBJECT, PER_QUESTION, Step, buildMock } from "@/src/misfire/mock/build";

type Chapter = { name: string; count: number };
type Pool = Record<Subject, { total: number; chapters: Chapter[] }>;
const QUICK = ["0", "5", "10", "15", "20", "25"];
const TINY: Record<Subject, string> = { Physics: "Phy", Chemistry: "Chem", Mathematics: "Maths" };
// Chapters in the order of their numbers ("01 Units…", "02 …"); the questions of papers without chapter names last.
const lead = (name: string) => { const m = /^(\d+)/.exec(name.trim()); return m ? Number(m[1]) : 999; };
const byChapter = (a: Chapter, b: Chapter) => (!chapterName(a.name) ? 1 : 0) - (!chapterName(b.name) ? 1 : 0) || lead(a.name) - lead(b.name) || a.name.localeCompare(b.name);

/** Every subject's open Misfire questions and their chapters (the first page of each subject carries both). */
async function loadPool(signal: AbortSignal): Promise<Pool> {
  const pages = await Promise.all(SUBJECTS.map((s) => getPage("open", s, "", 1, signal)));
  return Object.fromEntries(SUBJECTS.map((s, i) => [s, { total: pages[i].total || 0, chapters: (pages[i].chapters || []).filter((c) => c?.name && c.count > 0).sort(byChapter) }])) as Pool;
}

function ChapterRow({ c, on, onPress, testID }: { c: Chapter; on: boolean; onPress: () => void; testID: string }) {
  return <Press testID={testID} onPress={onPress} scaleTo={0.99} accessibilityRole="checkbox" accessibilityState={{ checked: on }}
    accessibilityLabel={`${chapterLabel(c.name)}, ${c.count} sawaal${on ? ", chuna hua" : ""}`} style={[styles.row, on && styles.rowOn]}>
    <Tick on={on} color={colors.custom_chipBlood} />
    <T w="heavy" size={14.5} numberOfLines={2} style={{ flex: 1 }}>{chapterLabel(c.name)}</T>
    <T w="bold" size={12} color={colors.muted}>{c.count}</T>
  </Press>;
}

export default function NewMisfireMock() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  if (user) misfireAccount(user.id);
  const pool = useCached<Pool>(user ? `${misfireKey(user.id)}.mockpool` : null, loadPool, false);
  const p = pool.data;
  const [subject, setSubject] = useState<Subject>("Physics");
  const [counts, setCounts] = useState<Counts>({ ...NONE });
  // `null`: every chapter of the subject; otherwise the chapters ticked.
  const [picked, setPicked] = useState<Record<Subject, string[] | null>>({ Physics: null, Chemistry: null, Mathematics: null });
  const [making, setMaking] = useState<{ step?: Step; error?: string } | null>(null);
  const stop = useRef<AbortController | null>(null);
  useEffect(() => () => stop.current?.abort(), []);

  const available = (s: Subject) => !p ? 0 : picked[s] === null ? p[s].total : p[s].chapters.filter((c) => picked[s]!.includes(c.name)).reduce((n, c) => n + c.count, 0);
  const most = (s: Subject) => Math.min(MAX_PER_SUBJECT, available(s));
  // A chapter unticked can leave fewer questions than were asked for: the count follows.
  useEffect(() => { if (p) setCounts((c) => { const next = { ...c }; for (const s of SUBJECTS) next[s] = Math.min(c[s], most(s)); return next; }); }, [p, picked]); // eslint-disable-line react-hooks/exhaustive-deps

  const total = totalOf(counts), minutes = minutesFor(counts, PER_QUESTION);
  const chapters = p?.[subject].chapters || [];
  const all = picked[subject] === null;
  const isOn = (name: string) => all || picked[subject]!.includes(name);
  function toggle(name: string) {
    const names = chapters.map((c) => c.name);
    const now = all ? names : picked[subject]!;
    const next = now.includes(name) ? now.filter((n) => n !== name) : [...now, name];
    setPicked((o) => ({ ...o, [subject]: next.length === names.length ? null : next }));
  }
  const setAll = () => setPicked((o) => ({ ...o, [subject]: all ? [] : null }));
  const setCount = (s: Subject, n: number) => setCounts((c) => ({ ...c, [s]: Math.max(0, Math.min(most(s), n)) }));

  async function make() {
    if (!user || !p || !total) return;
    stop.current?.abort();
    const ctl = new AbortController(); stop.current = ctl;
    setMaking({ step: { step: "pick", done: 0, total: 1 } });
    try {
      const sizes = Object.fromEntries(SUBJECTS.map((s) => [s, Object.fromEntries(p[s].chapters.map((c) => [c.name, c.count]))])) as Record<Subject, Record<string, number>>;
      const { mock, short } = await buildMock(user.id, { counts, chapters: picked, sizes }, (step) => { if (!ctl.signal.aborted) setMaking({ step }); }, ctl.signal);
      if (ctl.signal.aborted) return;
      if (!mock.questions.length) { setMaking({ error: "Chune hue chapters ke sawaal abhi nahi mil paaye. Thodi der mein dobara try karo, ya doosre chapter chuno." }); return; }
      setMaking(null);
      router.replace({ pathname: "/misfire/mock/[id]", params: { id: mock.id, short: short.length ? "1" : "" } } as any);
    } catch (e: any) {
      if (e?.name === "AbortError" || ctl.signal.aborted) return;
      setMaking({ error: e?.message || "Mock abhi nahi ban paaya. Internet dekh kar dobara try karo." });
    }
  }

  const empty = p && !SUBJECTS.some((s) => p[s].total > 0);
  const step = making?.step;
  return <ScreenMotion>
    <View testID="mock-new-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <ScreenHeader testID="mock-new-header" title="Misfire Mock banao" eyebrow="Apni galtiyon se mock" backTestID="mock-new-back"
        onBack={() => (router.canGoBack() ? router.back() : router.replace("/misfire" as any))} />
      <ScrollView contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: space.xl, gap: space.md }} showsVerticalScrollIndicator={false}>
        <ChoiceHero testID="mock-new-hero">
          <T w="heavy" size={11} color={ON_HERO.soft} style={heroStyles.kicker}>MISFIRE MOCK</T>
          <T w="heavy" size={22} color={ON_HERO.ink}>Apni galtiyon ka JEE Main mock</T>
          <T size={13} color={ON_HERO.soft}>Sirf woh sawaal jo aapse galat hue ya chhoot gaye. Har subject ke 25 tak: Physics 60, Chemistry 40, Maths 80 min.</T>
          {p ? <View style={heroStyles.counts}>
            {SUBJECTS.map((s, i) => <View key={s} style={[heroStyles.count, i > 0 && heroStyles.countLine]}>
              <T testID={`mock-new-open-${s.toLowerCase()}`} w="heavy" size={18} color={ON_HERO.ink}>{p[s].total}</T>
              <T size={11} color={ON_HERO.soft}>{SHORT[s]}</T>
            </View>)}
          </View> : null}
        </ChoiceHero>
        <ErrorBox testID="mock-new-error" error={pool.error && !p ? pool.error : ""} retry={pool.reload} />
        {!p && !pool.error ? <View testID="mock-new-loading" style={{ gap: space.sm }}><Skeleton h={52} /><Skeleton h={96} /><Skeleton h={64} /><Skeleton h={64} /></View> : null}
        {empty ? <DCard testID="mock-new-empty"><Empty icon="check-circle-outline" title="Misfire khaali hai." body="Koi galat ya chhoda sawaal nahi bacha. Agla paper do; jo galat ya chhoot jaye, yahan se mock ban jayega." /></DCard> : null}
        {p && !empty ? <>
          <SubjectTabs prefix="mock-subject" value={subject} onChange={setSubject} items={SUBJECTS.map((s) => ({ subject: s, count: counts[s] }))} />

          <DCard testID="mock-new-count" style={{ gap: space.md }}>
            <View style={styles.head}>
              <T w="heavy" size={10.5} color={colors.brandText} style={styles.kicker}>{SHORT[subject].toUpperCase()} · KITNE SAWAAL</T>
              <T testID="mock-new-most" size={12} color={colors.muted}>Max {most(subject)}</T>
            </View>
            <RedTabs prefix={`mock-count-${subject.toLowerCase()}`} value={String(counts[subject])} onChange={(k) => setCount(subject, Number(k))}
              items={QUICK.map((k) => ({ key: k, label: k === "0" ? "Nahi" : k, disabled: Number(k) > most(subject) }))} />
            <View style={styles.stepper}>
              <Press testID="mock-count-less" disabled={counts[subject] <= 0} onPress={() => setCount(subject, counts[subject] - 1)} accessibilityLabel="Ek sawaal kam" style={[styles.step, counts[subject] <= 0 && styles.off]}>
                <Icon name="minus" size={20} color={colors.onSurface} />
              </Press>
              <View style={{ flex: 1, alignItems: "center" }}>
                <T testID="mock-count-value" w="heavy" size={22}>{counts[subject]} <T size={13} color={colors.muted}>sawaal</T></T>
                <T testID="mock-count-time" size={12} color={colors.muted}>{counts[subject] ? `${timeLabel(minutesFor({ ...NONE, [subject]: counts[subject] }, PER_QUESTION))} · ${counts[subject] * MARKS.correct} marks` : "Is subject se nahi"}</T>
              </View>
              <Press testID="mock-count-more" disabled={counts[subject] >= most(subject)} onPress={() => setCount(subject, counts[subject] + 1)} accessibilityLabel="Ek sawaal zyada" style={[styles.step, counts[subject] >= most(subject) && styles.off]}>
                <Icon name="plus" size={20} color={colors.onSurface} />
              </Press>
            </View>
          </DCard>

          <View style={[styles.head, { marginTop: space.xs }]}>
            <T w="heavy" size={10.5} color={colors.brandText} style={styles.kicker}>{SHORT[subject].toUpperCase()} · CHAPTER CHUNO</T>
            <T size={12} color={colors.muted}>{available(subject)} sawaal</T>
          </View>
          {chapters.length ? <>
            <Press testID="mock-chapter-all" onPress={setAll} scaleTo={0.99} accessibilityRole="checkbox" accessibilityState={{ checked: all }}
              accessibilityLabel={`Select all chapters, ${SHORT[subject]}${all ? ", chuna hua" : ""}`} style={[styles.row, styles.allRow, all && styles.rowOn]}>
              <Tick on={all} color={colors.custom_chipBlood} />
              <View style={{ flex: 1, minWidth: 0 }}>
                <T w="heavy" size={15}>Select all chapters</T>
                <T size={12} color={colors.muted} numberOfLines={1}>{SHORT[subject]} ke saare {chapters.length} chapter · {p[subject].total} sawaal</T>
              </View>
            </Press>
            {chapters.map((c, i) => <ChapterRow key={c.name} testID={`mock-chapter-${i}`} c={c} on={isOn(c.name)} onPress={() => toggle(c.name)} />)}
            {!all && !picked[subject]!.length ? <T testID="mock-chapter-none" size={12.5} color={colors.brandText}>Kam se kam ek chapter chuno, ya is subject ki ginti “Nahi” rakho.</T> : null}
          </> : <DCard testID="mock-chapter-empty"><T size={13} color={colors.muted}>{SHORT[subject]} mein koi galat ya chhoda sawaal nahi hai.</T></DCard>}
        </> : null}
      </ScrollView>
      {p && !empty ? <StepBar testID="mock-new-bar" big={total ? `${total} sawaal · ${timeLabel(minutes)}` : "Ginti chuno"}
        small={total ? SUBJECTS.filter((s) => counts[s]).map((s) => `${TINY[s]} ${counts[s]}`).join(" · ") : "Upar ginti chuno"}
        label="Mock banao" disabled={!total} onPress={make} /> : null}

      <DSheet visible={!!making} onClose={() => { stop.current?.abort(); setMaking(null); }} testID="mock-making-sheet" title={making?.error ? "Mock nahi ban paaya" : "Mock ban raha hai"}>
        {making?.error ? <>
          <ErrorBox testID="mock-making-error" error={making.error} />
          <Pill testID="mock-making-retry" kind="brand" label="Dobara try karo" onPress={make} />
        </> : <View testID="mock-making-progress" style={{ gap: space.md }}>
          <View style={styles.progressRow}>
            <Icon name={step?.step === "keys" ? "key-variant" : "shuffle-variant"} size={20} color={colors.custom_chipBlood} />
            <T testID="mock-making-step" w="bold" size={14} style={{ flex: 1 }}>{step?.step === "keys" ? `Answer key aur solutions aa rahe hain · ${step.done}/${step.total} papers` : "Aapke Misfire se sawaal chun rahe hain…"}</T>
          </View>
          <View style={styles.track}><View style={[styles.fill, { width: `${step?.step === "keys" ? 20 + (80 * step.done) / Math.max(1, step.total) : 12}%` }]} /></View>
          <T size={12} color={colors.muted}>Jin papers ka result phone par rakha hai, woh wahin se aate hain. Website par kuch shuru nahi hota.</T>
        </View>}
        <Pill testID="mock-making-cancel" kind="outline" label={making?.error ? "Band karo" : "Ruko, wapas jao"} onPress={() => { stop.current?.abort(); setMaking(null); }} />
      </DSheet>
    </View>
  </ScreenMotion>;
}

const styles = StyleSheet.create({
  head: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.sm },
  kicker: { letterSpacing: 1.4 },
  stepper: { flexDirection: "row", alignItems: "center", gap: space.md },
  step: { width: 48, height: 48, borderRadius: 24, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, alignItems: "center", justifyContent: "center" },
  off: { opacity: 0.35 },
  row: { flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 58, paddingVertical: 10, paddingHorizontal: 14, borderRadius: 18, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card },
  allRow: { minHeight: 64 },
  rowOn: { borderColor: colors.custom_chipBlood, backgroundColor: colors.custom_chipBloodSoft },
  progressRow: { flexDirection: "row", alignItems: "center", gap: space.sm },
  track: { height: 6, borderRadius: radius.pill, backgroundColor: colors.custom_cardLine, overflow: "hidden" },
  fill: { height: 6, borderRadius: radius.pill, backgroundColor: colors.custom_chipBlood },
});
