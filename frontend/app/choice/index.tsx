// Student Choice (Home's fourth tile): the student makes their own paper. Two ways in: choose chapters and then questions
// (they are listed without options), or a random mock of as many questions as they ask for, mixed like a JEE Main paper.
// At most 75 questions; +4 / −1; the time comes from the subjects (Maths 3.2, Physics 2.4, Chemistry 1.6 minutes a
// question, so 25 + 25 + 25 get 180 minutes). jeelive.ai makes the paper, and from there it is an ordinary paper.
import React, { useRef, useState } from "react";
import { RefreshControl, ScrollView, StyleSheet, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { uuid } from "@/src/api/client";
import { useListFocus } from "@/src/useListFocus";
import { Empty, ErrorBox, IconName, Notice, Press, Skeleton, T } from "@/src/components/ui";
import { DCard, DSheet, IconCircle, Pill, ScreenHeader, SectionLabel } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { ScreenMotion } from "@/src/motion";
import { colors, fonts, noOutline, space, subjectColor } from "@/src/theme";
import { Bank, SHORT, makePaper, minutesFor, splitOf, timeLabel } from "@/src/choice/api";
import { Makeup, useBank } from "@/src/choice/parts";
import { pickedCount, useChoice } from "@/src/choice/store";

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
  useChoice();
  const [random, setRandom] = useState(false);
  const bank = res.data, chosen = pickedCount();
  return <ScreenMotion>
    <View testID="choice-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <ScreenHeader testID="choice-header" title="Student Choice" eyebrow="Apna paper khud banao" backTestID="choice-back"
        onBack={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)"))} />
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: insets.bottom + space.xxl, gap: space.lg }}
        refreshControl={<RefreshControl testID="choice-refresh" refreshing={res.refreshing} onRefresh={res.reload} />}>
        <View style={{ gap: space.sm }}>
          <T testID="choice-title" w="heavy" size={24} style={{ letterSpacing: -0.4 }}>Apna paper, apni marzi.</T>
          <T size={13.5} color={colors.muted} style={{ lineHeight: 20 }}>Chapters aur sawaal khud chuno, ya ek tap mein random mock lo. Result, analysis aur solutions har paper ki tarah milte hain.</T>
          <View style={styles.facts}>
            {[`${bank?.ready ? bank.max_questions : 75} sawaal tak`, "+4 / −1", "time subject ke hisaab se"].map(f => <View key={f} style={styles.fact}><T w="bold" size={11.5} color={colors.custom_softText}>{f}</T></View>)}
          </View>
        </View>
        <ErrorBox testID="choice-error" error={res.error} retry={res.reload} />
        {!bank ? (res.error ? null : <View testID="choice-loading" style={{ gap: space.md }}><Skeleton h={92} /><Skeleton h={92} /></View>)
          : !bank.ready ? <DCard testID="choice-not-ready"><Empty icon="database-search-outline" title="Sawaalon ka bank jud raha hai"
            body="Student Choice ke sawaal jeelive.ai ke chapter-wise sawaalon se aate hain. Jaise hi woh yahan jud jayenge, chapters dikhne lagenge. Tab tak chapter-wise tests se practice karo."
            action={<Pill testID="choice-open-chapters" label="Chapter-wise tests" iconRight="arrow-right" onPress={() => router.push("/catalogue?slug=jee-main&kind=chapters")} />} /></DCard>
            : <>
              {bank.sample ? <Notice testID="choice-sample" tone="warning">SAMPLE: yeh chapters aur sawaal sirf dikhane ke liye bane hain. Asli sawaal jeelive.ai se judte hi yahan aayenge; tab paper bhi banega.</Notice> : null}
              <View style={{ gap: space.md }}>
                <Way testID="choice-way-pick" icon="format-list-checks" title="Sawaal khud chuno" onPress={() => router.push("/choice/pick")}
                  body="Subject, phir chapters, phir sawaal. Sirf sawaal dikhte hain, options paper mein milte hain."
                  note={chosen ? `${chosen} sawaal chune hue hain · jaari rakho` : undefined} />
                <Way testID="choice-way-random" icon="creation" title="Random mock" onPress={() => setRandom(true)}
                  body="Bas sawaalon ki ginti batao. Physics, Chemistry aur Maths mile-jule aayenge, JEE Main ki tarah." />
              </View>
              <View style={{ gap: space.md }}>
                <SectionLabel title="Time kaise milta hai" />
                <DCard testID="choice-time" style={{ gap: 0, paddingVertical: space.xs }}>
                  {bank.subjects.map(s => <View key={s.name} style={styles.time}>
                    <View style={[styles.dot, { backgroundColor: subjectColor(s.name) }]} />
                    <T w="bold" size={14} style={{ flex: 1 }}>{SHORT[s.name]}</T>
                    <T size={12.5} color={colors.muted}>25 sawaal = </T>
                    <T w="heavy" size={14}>{timeLabel(Math.ceil(25 * bank.minutes[s.name]))}</T>
                  </View>)}
                  <T size={12} color={colors.muted} style={styles.timeNote}>Har sawaal apne subject ka time laata hai, isliye chhota paper chhota time paata hai. 25 + 25 + 25 sawaal = {timeLabel(minutesFor({ Physics: 25, Chemistry: 25, Mathematics: 25 }, bank.minutes))}.</T>
                </DCard>
              </View>
            </>}
      </ScrollView>
      {bank?.ready ? <DSheet testID="choice-random-sheet" visible={random} onClose={() => setRandom(false)} title="Random mock" keyboard>
        <RandomForm bank={bank} onMade={paper => { setRandom(false); router.push(`/set/${paper}`); }} />
      </DSheet> : null}
    </View>
  </ScreenMotion>;
}

const styles = StyleSheet.create({
  way: { flexDirection: "row", alignItems: "center", gap: space.md, padding: space.lg },
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
