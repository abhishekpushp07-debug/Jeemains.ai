// Student Choice (Home's fourth tile): the JEE Main chapter-wise questions, the student's own way. They tick chapters;
// what they can do with them depends on what the website can make (the bank says so, see src/choice/api.ts):
//   today        each ticked chapter's whole test, one after another (app/choice/tests.tsx);
//   bank.pick    choose questions of those chapters (listed without options) and have one paper made of them;
//   bank.random  a random mock of as many questions as they ask for, mixed like a JEE Main paper.
// A made paper has at most 75 questions, +4 / −1, and its time comes from the subjects (Maths 3.2, Physics 2.4,
// Chemistry 1.6 minutes a question, so 25 + 25 + 25 get 80 + 60 + 40 = 180 minutes). jeelive.ai makes the paper, and
// from there it is an ordinary paper.
import React, { useRef, useState } from "react";
import { RefreshControl, ScrollView, StyleSheet, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { uuid } from "@/src/api/client";
import { useListFocus } from "@/src/useListFocus";
import { Empty, ErrorBox, IconName, Notice, Press, Skeleton, T } from "@/src/components/ui";
import { DCard, DSheet, IconCircle, Pill, ScreenHeader, SectionLabel, StatusLine } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { ScreenMotion } from "@/src/motion";
import { colors, fonts, noOutline, space, subjectColor } from "@/src/theme";
import { Bank, SHORT, makePaper, minutesFor, splitOf, timeLabel } from "@/src/choice/api";
import { Makeup, useBank } from "@/src/choice/parts";
import { chosenChapters, pickedCount, useChoice } from "@/src/choice/store";

const QUICK = [15, 30, 45, 60, 75];

function Way({ icon, title, body, note, onPress, testID }: { icon: IconName; title: string; body: string; note?: string; onPress: () => void; testID: string }) {
  return <Press testID={testID} onPress={onPress} scaleTo={0.985} accessibilityLabel={`${title}. ${body}`}>
    <DCard style={styles.way}>
      <IconCircle icon={icon} color={colors.onSurface} bg={colors.custom_cardRaised} line={colors.custom_cardLine} size={48} />
      <View style={{ flex: 1, minWidth: 0, gap: 3 }}>
        <T w="heavy" size={16.5}>{title}</T>
        <T size={12.5} color={colors.muted} style={{ lineHeight: 18 }}>{body}</T>
        {note ? <T testID={`${testID}-note`} w="bold" size={12} color={colors.custom_mint}>{note}</T> : null}
      </View>
      <Glyph name="chevron-right" size={20} color={colors.muted} />
    </DCard>
  </Press>;
}

/** The random mock's sheet: only the number of questions is asked. Drawn only while the sheet is open. */
function RandomForm({ bank, onMade }: { bank: Bank; onMade: (paper: string) => void }) {
  const subjects = bank.subjects.map(s => s.name);
  // Never more than the bank can give: every subject has its own questions, and (when set) its own top.
  const room = bank.subjects.map(s => Math.min(s.chapters.reduce((n, c) => n + c.count, 0), bank.max_per_subject ?? Infinity));
  const most = Math.min(bank.max_questions, Math.min(...room) * subjects.length);
  const least = subjects.length;
  const [text, setText] = useState(String(Math.min(30, most)));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const asked = useRef({ n: 0, key: "" });
  const n = /^\d{1,3}$/.test(text) ? Number(text) : 0;
  const good = n >= least && n <= most;
  const split = splitOf(good ? n : 0, subjects);
  async function make() {
    if (!good || busy) return;
    if (asked.current.n !== n) asked.current = { n, key: uuid() }; // the same key for every retry of this one mock
    setBusy(true); setError("");
    try { onMade(await makePaper({ mode: "random", count: n }, asked.current.key)); } catch (e: any) { setError(e?.message || "Mock ban nahi paaya. Dobara try karo."); setBusy(false); }
  }
  return <>
    <T size={13} color={colors.custom_softText} style={{ lineHeight: 19 }}>Bas ginti batao. Sawaal {subjects.map(s => SHORT[s]).join(", ")} se barabar aur mile-jule aayenge, JEE Main ke paper ki tarah.</T>
    <View style={{ gap: 6 }}>
      <T w="bold" size={12} color={colors.custom_eyebrow}>Kitne sawaal? ({least} se {most})</T>
      <TextInput testID="choice-random-input" value={text} onChangeText={v => { setText(v.replace(/[^0-9]/g, "").slice(0, 3)); setError(""); }} keyboardType="number-pad" returnKeyType="done"
        maxLength={3} editable={!busy} onSubmitEditing={make} placeholder="30" placeholderTextColor={colors.custom_dim} accessibilityLabel="Kitne sawaal" style={[styles.input, noOutline]} />
      <View style={styles.quick}>
        {QUICK.filter(q => q <= most).map(q => <Press key={q} testID={`choice-random-quick-${q}`} onPress={() => { setText(String(q)); setError(""); }} accessibilityState={{ selected: n === q }}
          accessibilityLabel={`${q} sawaal`} style={[styles.chip, n === q && styles.chipOn]}>
          <T w="heavy" size={13.5} color={n === q ? colors.onSurfaceInverse : colors.custom_softText}>{q}</T>
        </Press>)}
      </View>
    </View>
    {good ? <Makeup testID="choice-random-makeup" counts={split} bank={bank} />
      : <T testID="choice-random-range" w="semibold" size={13} color={colors.error}>{least} se {most} ke beech ginti likho.</T>}
    {good ? <T testID="choice-random-rule" size={12.5} color={colors.muted}>Poore {n * bank.marks.correct} marks · sahi +{bank.marks.correct}, galat {bank.marks.wrong}, chhoda 0 · time {timeLabel(minutesFor(split, bank.minutes))}</T> : null}
    {error ? <Notice testID="choice-random-error" tone="error">{error}</Notice> : null}
    <Pill testID="choice-random-make" size="lg" icon="creation" label="Random mock banao" busy={busy} disabled={!good} onPress={make} style={good ? undefined : styles.off} />
  </>;
}

export default function StudentChoice() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const res = useBank(user?.id);
  useListFocus(res.revalidate);
  useChoice(user?.id);
  const [random, setRandom] = useState(false);
  const bank = res.data, open = bank?.ready ? bank : null, chosen = pickedCount();
  const all = open ? open.subjects.flatMap(s => s.chapters) : [];
  // Only chapters the bank still has count (one may have gone since it was ticked).
  const ticked = chosenChapters().filter(id => all.some(c => c.id === id)).length;
  const making = !!open && (!!open.pick || !!open.random); // the website can make a paper
  // A whole chapter test keeps the website's own time: said here when every test has the same.
  const testTimes = [...new Set(all.map(c => c.test?.minutes).filter(Boolean))];
  return <ScreenMotion>
    <View testID="choice-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <ScreenHeader testID="choice-header" title="Student Choice" eyebrow={making ? "Apna paper khud banao" : "Apne chapters, apni marzi"} backTestID="choice-back"
        onBack={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)"))} />
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: insets.bottom + space.xxl, gap: space.lg }}
        refreshControl={<RefreshControl testID="choice-refresh" refreshing={res.refreshing} onRefresh={res.reload} />}>
        <View style={{ gap: space.sm }}>
          <T testID="choice-title" w="heavy" size={24} style={{ letterSpacing: -0.4 }}>{making ? "Apna paper, apni marzi." : "Apne chapters, apni marzi."}</T>
          <T testID="choice-intro" size={13.5} color={colors.muted} style={{ lineHeight: 20 }}>{open?.pick ? "JEE Main ke chapter-wise sawaalon mein se chapters aur sawaal khud chuno. Result, analysis aur solutions har paper ki tarah milte hain."
            : "JEE Main ke chapter-wise sawaal, aapke chune chapters ke hisaab se. Result, analysis aur solutions har paper ki tarah milte hain."}</T>
          {open ? <View testID="choice-facts" style={styles.facts}>
            {(making ? [`${open.max_questions} sawaal tak`, `+${open.marks.correct} / −${Math.abs(open.marks.wrong)}`, "time subject ke hisaab se"]
              : [`${all.length} chapters`, `${all.reduce((n, c) => n + c.count, 0)} sawaal`, `+${open.marks.correct} / −${Math.abs(open.marks.wrong)}`]).map(f => <View key={f} style={styles.fact}><T w="bold" size={11.5} color={colors.custom_softText}>{f}</T></View>)}
          </View> : null}
        </View>
        <ErrorBox testID="choice-error" error={res.error} retry={res.reload} />
        {!bank ? (res.error ? null : <View testID="choice-loading" style={{ gap: space.md }}><Skeleton h={92} /><Skeleton h={92} /></View>)
          : !open ? <DCard testID="choice-not-ready"><Empty icon="database-search-outline" title="Chapters abhi nahi mile"
            body="Student Choice ke sawaal JEE Main ke chapter-wise sawaal hi hain. Abhi koi chapter khula nahi mila. Thodi der mein dobara dekho, ya chapter-wise tests kholo."
            action={<Pill testID="choice-open-chapters" label="Chapter-wise tests" iconRight="arrow-right" onPress={() => router.push("/catalogue?slug=jee-main&kind=chapters")} />} /></DCard>
            : <>
              {open.sample ? <Notice testID="choice-sample" tone="warning">SAMPLE: yeh chapters aur sawaal sirf dikhane ke liye bane hain. Asli chapters ke saath paper jeelive.ai banayega.</Notice> : null}
              <View style={{ gap: space.md }}>
                {open.pick ? <Way testID="choice-way-pick" icon="format-list-checks" title="Sawaal khud chuno" onPress={() => router.push("/choice/pick")}
                  body="Subject, phir chapters, phir sawaal. Sirf sawaal dikhte hain, options paper mein milte hain."
                  note={chosen ? `${chosen} sawaal chune hue hain · jaari rakho` : undefined} />
                  : <Way testID="choice-way-chapters" icon="format-list-checks" title="Chapters chuno" onPress={() => router.push("/choice/pick")}
                    body="Physics, Chemistry aur Maths ke chapters tick karo. Har chune chapter ka poora test milega: ek-ek karke do."
                    note={ticked ? `${ticked} chapter${ticked === 1 ? "" : "s"} chune hue hain` : undefined} />}
                {!open.pick && ticked ? <Way testID="choice-way-tests" icon="clipboard-text-outline" title="Aapke chapter tests" onPress={() => router.push("/choice/tests")}
                  body={`Chune hue ${ticked} chapter${ticked === 1 ? "" : "s"} ke test: shuru karo, jaari rakho ya result dekho.`} /> : null}
                {open.random ? <Way testID="choice-way-random" icon="creation" title="Random mock" onPress={() => setRandom(true)}
                  body="Bas sawaalon ki ginti batao. Physics, Chemistry aur Maths mile-jule aayenge, JEE Main ki tarah." /> : null}
              </View>
              {!open.pick || !open.random ? <DCard testID="choice-soon" style={styles.soon}>
                <StatusLine testID="choice-soon-label" color={colors.custom_timerAmber} label="Jald aa raha hai" />
                {!open.pick ? <T testID="choice-soon-pick" size={13} color={colors.custom_softText} style={{ lineHeight: 19 }}><T w="heavy" size={13}>Sawaal khud chunna. </T>
                  Chune chapters ke sawaal dekho (bina options), jo chahiye tick karo, aur un sab ka ek hi paper banao: {open.max_questions} sawaal tak.</T> : null}
                {!open.random ? <T testID="choice-soon-random" size={13} color={colors.custom_softText} style={{ lineHeight: 19 }}><T w="heavy" size={13}>Random mock. </T>
                  Bas ginti batao; Physics, Chemistry aur Maths ke sawaal mile-jule aayenge, JEE Main ki tarah.</T> : null}
                <T size={12} color={colors.muted} style={{ lineHeight: 17 }}>Khulte hi yahin dikhega, app update kiye bina.</T>
              </DCard> : null}
              <View style={{ gap: space.md }}>
                <SectionLabel title={making ? "Time kaise milta hai" : "Banaye hue paper ka time"} />
                <DCard testID="choice-time" style={{ gap: 0, paddingVertical: space.xs }}>
                  {open.subjects.map(s => <View key={s.name} testID={`choice-time-${s.name.toLowerCase()}`} style={styles.time}>
                    <View style={[styles.dot, { backgroundColor: subjectColor(s.name) }]} />
                    <T w="bold" size={14} style={{ flex: 1 }}>{SHORT[s.name]}</T>
                    <T size={12.5} color={colors.muted}>25 sawaal = </T>
                    <T w="heavy" size={14}>{timeLabel(Math.ceil(25 * open.minutes[s.name]))}</T>
                  </View>)}
                  <T testID="choice-time-note" size={12} color={colors.muted} style={styles.timeNote}>Har sawaal apne subject ka time laata hai, isliye chhota paper chhota time paata hai. 25 + 25 + 25 sawaal = {timeLabel(minutesFor({ Physics: 25, Chemistry: 25, Mathematics: 25 }, open.minutes))}.{making ? ""
                    : ` Yeh time aapke banaye paper par lagega (sawaal chunna aur random mock). Poore chapter test ka time uske page par likha hota hai${testTimes.length === 1 ? ` (abhi ${timeLabel(testTimes[0] as number)})` : ""}.`}</T>
                </DCard>
              </View>
            </>}
      </ScrollView>
      {open?.random ? <DSheet testID="choice-random-sheet" visible={random} onClose={() => setRandom(false)} title="Random mock" keyboard>
        <RandomForm bank={open} onMade={paper => { setRandom(false); router.push(`/set/${paper}`); }} />
      </DSheet> : null}
    </View>
  </ScreenMotion>;
}

const styles = StyleSheet.create({
  way: { flexDirection: "row", alignItems: "center", gap: space.md, padding: space.lg },
  soon: { gap: space.sm, padding: space.lg },
  facts: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 4 },
  fact: { height: 28, paddingHorizontal: 11, borderRadius: 14, justifyContent: "center", backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLine },
  time: { flexDirection: "row", alignItems: "center", gap: space.sm, minHeight: 44 },
  timeNote: { lineHeight: 17, paddingTop: 6, paddingBottom: space.sm },
  dot: { width: 8, height: 8, borderRadius: 4 },
  input: { minHeight: 54, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, paddingHorizontal: space.lg,
    fontFamily: fonts.heavy, fontSize: 22, color: colors.onSurface },
  quick: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: { minWidth: 52, height: 44, paddingHorizontal: 14, borderRadius: 22, alignItems: "center", justifyContent: "center", borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card },
  chipOn: { backgroundColor: colors.onSurface, borderColor: colors.onSurface },
  off: { opacity: 0.4 },
});
