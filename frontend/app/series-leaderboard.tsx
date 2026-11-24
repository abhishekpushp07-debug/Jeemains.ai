// AITS Leaderboard: the All India Rank list of every series day the student has handed in. Pick a day, then one of three
// parts: Toppers (the top three on a podium and the top ten), Aas-paas (the students next to you) and Dhoondo (find
// anyone by name or Rank). Every number is the website's own leaderboard of that day's paper; the phone only works out
// how many marks a neighbour is ahead of or behind you. Reached from the series page; back returns there.
import React, { useState } from "react";
import { StyleSheet, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { Empty, ErrorBox, Icon, Skeleton, T } from "@/src/components/ui";
import { DCard, Pill, ScreenHeader, SectionLabel } from "@/src/components/design";
import { GlossTabs, TabLook } from "@/src/components/GlossTabs";
import { DayStrip } from "@/src/components/series/DayCards";
import { Board, BoardRow, BoardRows, Podium, YouCard, grouped } from "@/src/components/series/Board";
import { forgetBoard, useBoard } from "@/src/analysis/Leaderboard";
import { RANK_NOTE, r1 } from "@/src/analysis/format";
import { ScreenMotion } from "@/src/motion";
import { istDate } from "@/src/navigation";
import { colors, fonts, noOutline, radius, space, tabEdges } from "@/src/theme";
import { DayInfo, dayAttempt, istTime, useSeriesData } from "@/src/series";

type Part = "top" | "around" | "find";
// The three parts wear My Tests' glossy tab colours: yellow for the toppers, baby pink for your neighbours, sky blue for the search.
const LOOK: Record<Part, TabLook> = {
  top: { on: [colors.custom_tabSun, colors.custom_tabSunDeep], rest: [colors.custom_tabSunSoft, colors.custom_tabSunSoftDeep], edge: tabEdges.sun, glow: colors.custom_tabSunGlow },
  around: { on: [colors.custom_tabPink, colors.custom_tabPinkDeep], rest: [colors.custom_tabPinkSoft, colors.custom_tabPinkSoftDeep], edge: tabEdges.pink, glow: colors.custom_tabPinkGlow },
  find: { on: [colors.custom_tabSky, colors.custom_tabSkyDeep], rest: [colors.custom_tabSkySoft, colors.custom_tabSkySoftDeep], edge: tabEdges.sky, glow: colors.custom_tabSkyGlow },
};

export default function SeriesLeaderboard() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const { series, history, days, reload } = useSeriesData(user?.id);
  // A day is listed once its paper is handed in: scored, or sealed until that day's result opens.
  const done = days.filter(d => { const a = dayAttempt(d); return !!a && !a.resumable; });
  const [picked, setPicked] = useState<number | null>(null);
  const [part, setPart] = useState<Part>("top");
  const [asked, setAsked] = useState(0);
  // Opens on the newest day whose result is out.
  const day = done.find(d => d.day === picked) ?? [...done].reverse().find(d => !!dayAttempt(d)!.summary) ?? done[done.length - 1];
  const attempt = day ? dayAttempt(day)! : null;
  const error = (!series.data && series.error) || (!history.data && history.error) || "";
  const loading = !error && (!series.data || !history.data);
  const back = () => (router.canGoBack() ? router.back() : router.replace("/live"));

  return (
    // The shine rests while another screen is in front.
    <ScreenMotion>
      <View testID="aits-board-screen" style={[styles.screen, { paddingTop: insets.top + space.sm }]}>
        <ScreenHeader testID="aits-board-header" title="AITS Leaderboard" eyebrow="All India Series · har din" backTestID="aits-board-back" onBack={back} />
        <KeyboardAwareScrollView bottomOffset={24} keyboardShouldPersistTaps="handled" contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + space.xxl }]}>
          <ErrorBox error={error} retry={reload} testID="aits-board-load-error" />
          {loading ? <><Skeleton h={76} style={styles.soft} /><Skeleton h={168} style={styles.soft} /><Skeleton h={52} style={styles.round} /><Skeleton h={240} style={styles.soft} /></>
            : error ? null
            : !day || !attempt ? <DCard testID="aits-board-empty"><Empty icon="trophy" title="Abhi koi AITS paper submit nahi hua." body="Kisi live din ka paper do. Us din ka result khulte hi poore India ka leaderboard yahan aa jayega." /></DCard>
            : <>
              <SectionLabel title="Din chuno" right={<T testID="aits-board-days" size={12} color={colors.muted}>{done.length} din diye</T>} />
              <DayStrip prefix="aits-board" days={done} selected={day.day} onSelect={d => setPicked(d.day)} />
              {!attempt.summary && attempt.status === "embargoed"
                ? <DCard testID="aits-board-sealed" style={styles.wait}>
                  <T w="heavy" size={16}>Day {day.day} ka result {istTime(day.slot.closes_at)} par khulega.</T>
                  <T size={13} color={colors.muted}>Leaderboard result ke saath hi aata hai, jab sabka time khatam ho jaata hai.</T>
                </DCard>
                : <DayBoard key={`${attempt.id}:${asked}`} day={day} part={part} onPart={setPart} onRetry={() => { forgetBoard(attempt.id); setAsked(n => n + 1); }} />}
            </>}
        </KeyboardAwareScrollView>
      </View>
    </ScreenMotion>
  );
}

/** One day's leaderboard: your Rank card, the three parts and the part that is open. */
function DayBoard({ day, part, onPart, onRetry }: { day: DayInfo; part: Part; onPart: (p: Part) => void; onRetry: () => void }) {
  const a = dayAttempt(day)!;
  const d: Board | null = useBoard(a.id);
  const [all, setAll] = useState(false);
  if (!d) return <><Skeleton h={168} style={styles.soft} /><Skeleton h={52} style={styles.round} /><Skeleton h={240} style={styles.soft} /></>;
  if (d.state !== "ready") return <DCard testID="aits-board-wait" style={styles.wait}>
    <T w="heavy" size={16}>{d.state === "error" ? "Leaderboard nahi khul paaya." : "Is din ka leaderboard abhi taiyaar nahi hai."}</T>
    <T testID="aits-board-wait-note" size={13} color={colors.muted}>{d.state === "error" ? "Internet dekh kar dobara try karo." : RANK_NOTE[d.state] || "Thodi der mein dobara dekho."}</T>
    <Pill testID="aits-board-retry" kind="outline" size="sm" icon="refresh" label="Dobara dekho" onPress={onRetry} />
  </DCard>;

  const rows: BoardRow[] = d.rows || [], around: BoardRow[] = d.around || [], you = d.you || null;
  const shown = all ? rows : rows.slice(0, 10);
  // The nearest student ahead of you that the website sent: how many marks to the next step up.
  const ahead = you ? [...around, ...rows].filter(r => r.rank < you.rank).sort((x, y) => y.rank - x.rank)[0] : undefined;
  const gap = you && ahead ? r1(ahead.score - you.score) : 0;
  const tabs: { key: Part; label: string; look: TabLook; sub: string }[] = [
    { key: "top", label: "Toppers", look: LOOK.top, sub: String(Math.min(10, rows.length)) },
    { key: "around", label: "Aas-paas", look: LOOK.around, sub: you ? `#${you.rank}` : "—" },
    { key: "find", label: "Dhoondo", look: LOOK.find, sub: grouped(d.n) },
  ];

  return <>
    <YouCard live={a.mode === "series_live"} kicker={`DAY ${day.day} · ${istDate(day.date).toUpperCase()} · ${a.mode === "series_live" ? "LIVE" : "PRACTICE"}`} you={you} n={d.n} maximum={a.summary?.maximum} />
    <GlossTabs prefix="aits-board-tab" value={part} onChange={onPart} items={tabs} />
    {part === "top" ? <>
      <Podium rows={rows} title={d.title} />
      {shown.length > 3 ? <BoardRows testID="aits-board-top" rows={shown.slice(3)} /> : null}
      {rows.length > 10 ? <Pill testID="aits-board-more" kind="outline" size="sm" label={all ? "Sirf top 10 dikhao" : `Top ${rows.length} dikhao`} onPress={() => setAll(v => !v)} /> : null}
      {you && !shown.some(r => r.is_you) ? <>
        <T w="bold" size={11} color={colors.custom_eyebrow} style={styles.caps}>AAP YAHAN HO</T>
        <BoardRows testID="aits-board-top-you" rows={[you]} />
      </> : null}
    </> : part === "around" ? <>
      {you && (you.rank === 1 || gap > 0) ? <T testID="aits-board-next" w="bold" size={13} color={colors.custom_softText}>
        {you.rank === 1 ? "Is din aap sabse upar ho." : `Rank #${ahead!.rank} aapse ${gap} marks aage hai.`}</T> : null}
      {around.length ? <BoardRows testID="aits-board-around" rows={around} you={you} />
        : <T testID="aits-board-around-none" size={13} color={colors.muted}>Aapke aas-paas ke students tab dikhte hain jab is din ka aapka Rank ban jaata hai.</T>}
    </> : <Find id={a.id} />}
    <T size={11.5} color={colors.custom_eyebrow}>Har student ka pehla attempt gina jaata hai. Sirf naam, Score aur totals dikhte hain; kisi ke jawab ya phone number kabhi nahi.</T>
  </>;
}

/** Find any student of the day by name or Rank. The website does the search. */
function Find({ id }: { id: string }) {
  const [q, setQ] = useState("");
  const term = q.trim();
  return <>
    <View style={styles.search}>
      <Icon name="magnify" size={18} color={colors.custom_softText} />
      <TextInput testID="aits-board-search" value={q} onChangeText={t => setQ(t.slice(0, 20))} placeholder="Naam ya Rank likho" placeholderTextColor={colors.custom_dim}
        accessibilityLabel="Leaderboard mein dhoondo" autoCorrect={false} returnKeyType="search" style={[styles.input, noOutline]} />
    </View>
    {term ? <Found key={term} id={id} term={term} />
      : <T testID="aits-board-find-hint" size={13} color={colors.muted}>Kisi bhi student ka naam ya Rank likho. Jaise: Arjun, ya 25.</T>}
  </>;
}

/** The answer for one search term. A new term starts a new look-up, so an older answer is never shown under it. */
function Found({ id, term }: { id: string; term: string }) {
  const d: Board | null = useBoard(id, term);
  if (!d) return <Skeleton h={60} style={styles.soft} />;
  if (d.state === "error") return <T testID="aits-board-find-error" size={13} color={colors.error}>Dhoondh nahi paaye. Internet dekh kar dobara likho.</T>;
  const found = d.found || [];
  return found.length ? <BoardRows testID="aits-board-found" rows={found} />
    : <T testID="aits-board-none" size={13} color={colors.muted}>Is naam ya Rank ka koi student nahi mila.</T>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.surface },
  content: { padding: space.lg, paddingTop: space.xs, gap: space.md },
  soft: { borderRadius: 22 }, round: { borderRadius: radius.pill },
  wait: { gap: space.sm },
  caps: { letterSpacing: 1.6, marginTop: space.xs },
  search: { flexDirection: "row", alignItems: "center", gap: 8, minHeight: 48, paddingHorizontal: space.md, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_bar },
  input: { flex: 1, minHeight: 46, fontFamily: fonts.medium, fontSize: 14, color: colors.onSurface, paddingVertical: 0 },
});
