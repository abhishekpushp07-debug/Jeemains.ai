// AITS Leaderboard: the All India Rank list of every series day the student has handed in. Pick a day, then one of three
// parts: Toppers (the top three on a podium and the top ten), Aas-paas (the students next to you) and Dhoondo (find
// anyone by name or Rank). Every number is the website's own leaderboard of that day's paper; the phone only works out
// how many marks a neighbour is ahead of or behind you. Reached from the series page; back returns there.
// From the pink Rank card the student can write the name the leaderboards show ("Naam badlo") and share the Rank as a picture.
// "Poori series" (every live day's Score added up) appears next to "Har din" only once the website sends that leaderboard.
// A tap on any other student (a row or a podium step) puts that student's totals next to yours ("Aap vs").
// ?day=<day number> opens it on that day (the Rank journey graph on the series page sends it).
import React, { useCallback, useEffect, useRef, useState } from "react";
import { StyleSheet, TextInput, View, useWindowDimensions } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { ErrorBox, Icon, Skeleton, T } from "@/src/components/ui";
import { Pill, ScreenHeader, SectionLabel } from "@/src/components/design";
import { GlossTabs, TabLook } from "@/src/components/GlossTabs";
import { Shine } from "@/src/analysis/Shine";
import { DayStrip } from "@/src/components/series/DayCards";
import { Board, BoardRow, BoardRows, NoticeCard, Podium, YouCard, grouped, isSeriesBoard, pageSeen } from "@/src/components/series/Board";
import { NameSheet } from "@/src/components/series/NameSheet";
import { VersusSheet } from "@/src/components/series/VersusSheet";
import { SERIES_BOARD, forgetBoard, forgetBoards, useBoard } from "@/src/analysis/Leaderboard";
import { RANK_NOTE, r1 } from "@/src/analysis/format";
import { ScreenMotion } from "@/src/motion";
import { istDate } from "@/src/navigation";
import { colors, fonts, noOutline, pastel, radius, space, tabEdges } from "@/src/theme";
import { DayInfo, dayAttempt, istTime, useSeriesData } from "@/src/series";

type Part = "top" | "around" | "find";
type Scope = "day" | "all";
// The leaderboard name last heard from the website in this run of the app (and whose it is), so coming back to the screen shows it at once.
const heard: { uid?: string; name?: string } = {};
// "Har din" / "Poori series" wear My Tests' baby pink: full when open, a softer wash when not.
const SCOPE_LOOK: TabLook = { on: [colors.custom_tabPink, colors.custom_tabPinkDeep], rest: [colors.custom_tabPinkSoft, colors.custom_tabPinkSoftDeep], edge: tabEdges.pink, glow: colors.custom_tabPinkGlow };
// The three parts are glossy tabs, each in its own colour: yellow for the toppers, orange for your neighbours, sky blue
// for the search. The rows under a tab wear that tab's own soft colours and running edge.
const LOOK: Record<Part, TabLook> = {
  top: { on: [colors.custom_tabSun, colors.custom_tabSunDeep], rest: [colors.custom_tabSunSoft, colors.custom_tabSunSoftDeep], edge: tabEdges.sun, glow: colors.custom_tabSunGlow },
  around: { on: [colors.custom_tabOrange, colors.custom_tabOrangeDeep], rest: [colors.custom_tabOrangeSoft, colors.custom_tabOrangeSoftDeep], edge: tabEdges.orange, glow: colors.custom_tabOrangeGlow },
  find: { on: [colors.custom_tabSky, colors.custom_tabSkyDeep], rest: [colors.custom_tabSkySoft, colors.custom_tabSkySoftDeep], edge: tabEdges.sky, glow: colors.custom_tabSkyGlow },
};

export default function SeriesLeaderboard() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const { height } = useWindowDimensions();
  const top = useRef(0); // how far the page is scrolled
  useEffect(() => { pageSeen(top.current, height); }, [height]);
  const { series, history, days, reload } = useSeriesData(user?.id);
  // A day is listed once its paper is handed in: scored, or sealed until that day's result opens.
  const done = days.filter(d => { const a = dayAttempt(d); return !!a && !a.resumable; });
  const { day: dayParam } = useLocalSearchParams<{ day?: string }>();
  const [picked, setPicked] = useState<number | null>(dayParam ? Number(dayParam) : null);
  const [part, setPart] = useState<Part>("top");
  // What is typed in Dhoondo lives here, not in the day's own view, so it stays when the day is changed: the same name is
  // then looked up in the new day ("Aap vs" sends a name here to follow it from day to day).
  const [find, setFind] = useState("");
  const [asked, setAsked] = useState(0);
  // The whole-series leaderboard (every live day added up) shows by itself the day the website starts sending it; until
  // then the website answers 404 and nothing of it is drawn.
  const overall = useBoard(SERIES_BOARD);
  const [scope, setScope] = useState<Scope>("day");
  const whole = isSeriesBoard(overall) && scope === "all";
  // The name the leaderboards show for this student ("" = none yet), as last heard from the website; and what the last change did.
  const [name, setName] = useState<string | undefined>(heard.uid === user?.id ? heard.name : user?.display_name ?? undefined);
  const hear = useCallback((n: string) => { heard.uid = user?.id; heard.name = n; setName(n); }, [user?.id]);
  const [naming, setNaming] = useState(false);
  const [note, setNote] = useState("");
  // Opens on the newest day whose result is out.
  const day = done.find(d => d.day === picked) ?? [...done].reverse().find(d => !!dayAttempt(d)!.summary) ?? done[done.length - 1];
  const attempt = day ? dayAttempt(day)! : null;
  const error = (!series.data && series.error) || (!history.data && history.error) || "";
  const loading = !error && (!series.data || !history.data);
  const back = () => (router.canGoBack() ? router.back() : router.replace("/live"));
  const again = (id: string) => { forgetBoard(id); setAsked(n => n + 1); };
  // A new name is on every leaderboard at once: all of them are asked again.
  const saved = (kept: string) => {
    setNaming(false); hear(kept); forgetBoards(); setAsked(n => n + 1);
    setNote(kept ? `Naam save ho gaya. Leaderboard par ab “${kept}” dikhega.` : "Naam hat gaya. Leaderboard par aap phir se Learner dikhoge.");
  };
  const share = (params: { id: string; day?: string }) => router.push({ pathname: "/series-share", params } as any);
  const board = { part, onPart: setPart, find, onFind: setFind, name, note, onHear: hear, onName: () => setNaming(true) };

  return (
    // The shine rests while another screen is in front.
    <ScreenMotion>
      <View testID="aits-board-screen" style={[styles.screen, { paddingTop: insets.top + space.sm }]}>
        <ScreenHeader testID="aits-board-header" title="AITS Leaderboard" eyebrow={whole ? "All India Series · poori series" : "All India Series · har din"} backTestID="aits-board-back" onBack={back} />
        {/* Every scroll says which slice of the page shows, so only the rows on screen keep their shine moving. */}
        <KeyboardAwareScrollView bottomOffset={24} keyboardShouldPersistTaps="handled" onScroll={e => { top.current = e.nativeEvent.contentOffset.y; pageSeen(top.current, e.nativeEvent.layoutMeasurement.height); }}
          contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + space.xxl }]}>
          <ErrorBox error={error} retry={reload} testID="aits-board-load-error" />
          {loading ? <><Skeleton h={76} style={styles.soft} /><Skeleton h={168} style={styles.soft} /><Skeleton h={52} style={styles.round} /><Skeleton h={240} style={styles.soft} /></>
            : error ? null
            : <>
              {isSeriesBoard(overall) ? <GlossTabs prefix="aits-board-scope" value={scope} onChange={s => { setScope(s); setNote(""); }}
                items={[{ key: "day", label: "Har din", look: SCOPE_LOOK }, { key: "all", label: "Poori series", look: SCOPE_LOOK }]} /> : null}
              {whole ? <BoardView key={`all:${asked}`} {...board} onRetry={() => again(SERIES_BOARD)} onShare={() => share({ id: SERIES_BOARD })} />
                : !day || !attempt ? <NoticeCard testID="aits-board-empty" icon="trophy" title="Abhi koi AITS paper submit nahi hua." note="Kisi live din ka paper do. Us din ka result khulte hi poore India ka leaderboard yahan aa jayega." />
                : <>
                  <SectionLabel title="Din chuno" right={<T testID="aits-board-days" size={12} color={colors.muted}>{done.length} din diye</T>} />
                  <DayStrip prefix="aits-board" days={done} selected={day.day} onSelect={d => { setPicked(d.day); setNote(""); }} />
                  {!attempt.summary && attempt.status === "embargoed"
                    ? <NoticeCard testID="aits-board-sealed" icon="lock-clock" title={`Day ${day.day} ka result ${istTime(day.slot.closes_at)} par khulega.`} note="Leaderboard result ke saath hi aata hai, jab sabka time khatam ho jaata hai." />
                    : <BoardView key={`${attempt.id}:${asked}`} day={day} {...board} onRetry={() => again(attempt.id)} onShare={() => share({ id: attempt.id, day: String(day.day) })} />}
                </>}
            </>}
        </KeyboardAwareScrollView>
        <NameSheet visible={naming} current={name ?? ""} onClose={() => setNaming(false)} onSaved={saved} />
      </View>
    </ScreenMotion>
  );
}

// What changes between a day's leaderboard and the whole series'.
const WORDS = {
  day: { wait: "Is din ka leaderboard abhi taiyaar nahi hai.", none: "Is din ke leaderboard mein aapka Rank nahi hai.", first: "Is din aap sabse upar ho.",
    around: "Aapke aas-paas ke students tab dikhte hain jab is din ka aapka Rank ban jaata hai.", foot: "Har student ka pehla attempt gina jaata hai." },
  all: { wait: "Poori series ka leaderboard abhi taiyaar nahi hai.", none: "Poori series ke leaderboard mein aapka Rank abhi nahi hai.", first: "Poori series mein aap sabse upar ho.",
    around: "Aapke aas-paas ke students tab dikhte hain jab poori series ka aapka Rank ban jaata hai.", foot: "Har live din ka Score joda jaata hai; practice attempt nahi judte." },
};

/** One leaderboard: a day's (`day`), or the whole series' (no `day`). Your Rank card, the three parts and the part that is open. */
function BoardView({ day, part, onPart, find, onFind, onRetry, name, note, onHear, onName, onShare }: {
  day?: DayInfo; part: Part; onPart: (p: Part) => void; find: string; onFind: (q: string) => void; onRetry: () => void; name?: string; note: string; onHear: (name: string) => void; onName: () => void; onShare: () => void;
}) {
  const a = day ? dayAttempt(day)! : null;
  const id = a ? a.id : SERIES_BOARD;
  const words = a ? WORDS.day : WORDS.all;
  const d: Board | null = useBoard(id);
  const [all, setAll] = useState(false);
  const [versus, setVersus] = useState<BoardRow | null>(null); // the student whose totals stand next to yours
  const you = d?.state === "ready" ? d.you || null : null;
  // Your own row says which name the leaderboards show for you; the screen remembers it for a day where you have no Rank.
  const mine = you ? (you.named ? you.name : "") : undefined;
  useEffect(() => { if (mine !== undefined) onHear(mine); }, [mine, onHear]);
  if (!d) return <><Skeleton h={168} style={styles.soft} /><Skeleton h={52} style={styles.round} /><Skeleton h={240} style={styles.soft} /></>;
  if (d.state !== "ready") {
    const failed = d.state === "error";
    return <NoticeCard testID="aits-board-wait" noteTestID="aits-board-wait-note" icon={failed ? "wifi-off" : "timer-sand"}
      title={failed ? "Leaderboard nahi khul paaya." : words.wait}
      note={failed ? "Internet dekh kar dobara try karo." : RANK_NOTE[d.state] || "Thodi der mein dobara dekho."}>
      <Pill testID="aits-board-retry" size="sm" icon="refresh" label="Dobara dekho" bg={colors.custom_pastelInk} ink={pastel.upcoming.cta} onPress={onRetry} />
    </NoticeCard>;
  }

  const rows: BoardRow[] = d.rows || [], around: BoardRow[] = d.around || [];
  const shown = all ? rows : rows.slice(0, 10);
  // The nearest student ahead of you that the website sent: how many marks to the next step up.
  const ahead = you ? [...around, ...rows].filter(r => r.rank < you.rank).sort((x, y) => y.rank - x.rank)[0] : undefined;
  const gap = you && ahead ? r1(ahead.score - you.score) : 0;
  // With a Rank of your own, a tap on any other student compares the two of you.
  const pick = you ? setVersus : undefined;
  const tabs: { key: Part; label: string; look: TabLook; sub: string }[] = [
    { key: "top", label: "Toppers", look: LOOK.top, sub: String(Math.min(10, rows.length)) },
    { key: "around", label: "Aas-paas", look: LOOK.around, sub: you ? `#${you.rank}` : "—" },
    { key: "find", label: "Dhoondo", look: LOOK.find, sub: grouped(d.n) },
  ];

  return <>
    <YouCard kicker={a ? `DAY ${day!.day} · ${istDate(day!.date).toUpperCase()} · ${a.mode === "series_live" ? "LIVE" : "PRACTICE"}` : `POORI SERIES · ${d.days_counted} DIN JODE`}
      label={!a ? "Poori series mein aapka Rank" : a.mode === "series_live" ? "Aapka All India Rank" : "Is paper mein aapka Rank"} none={words.none}
      you={you} n={d.n} maximum={a ? a.summary?.maximum : d.maximum} counted={d.days_counted} name={mine ?? name} onName={onName} onShare={onShare} />
    {note ? <T testID="aits-board-name-note" w="bold" size={12.5} color={colors.custom_royalMid}>{note}</T> : null}
    <GlossTabs prefix="aits-board-tab" value={part} onChange={onPart} items={tabs} />
    {pick ? <T testID="aits-board-compare-hint" size={12} color={colors.custom_eyebrow}>Kisi bhi student par tap karo: aap aur woh, side by side.</T> : null}
    {part === "top" ? <>
      <Podium rows={rows} title={d.title} onPick={pick} />
      {shown.length > 3 ? <BoardRows testID="aits-board-top" rows={shown.slice(3)} look={LOOK.top} onPick={pick} /> : null}
      {rows.length > 10 ? <Pill testID="aits-board-more" kind="outline" size="sm" label={all ? "Sirf top 10 dikhao" : `Top ${rows.length} dikhao`} onPress={() => setAll(v => !v)} /> : null}
      {you && !shown.some(r => r.is_you) ? <>
        <T w="bold" size={11} color={colors.custom_eyebrow} style={styles.caps}>AAP YAHAN HO</T>
        <BoardRows testID="aits-board-top-you" rows={[you]} look={LOOK.top} />
      </> : null}
    </> : part === "around" ? <>
      {you && (you.rank === 1 || gap > 0) ? <T testID="aits-board-next" w="bold" size={13} color={colors.custom_softText}>
        {you.rank === 1 ? words.first : `Rank #${ahead!.rank} aapse ${gap} marks aage hai.`}</T> : null}
      {around.length ? <BoardRows testID="aits-board-around" rows={around} you={you} look={LOOK.around} onPick={pick} />
        : <T testID="aits-board-around-none" size={13} color={colors.muted}>{words.around}</T>}
    </> : <Find id={id} q={find} onQ={onFind} you={you} daily={!!a} onPick={pick} />}
    <T testID="aits-board-foot" size={11.5} color={colors.custom_eyebrow}>{words.foot} Sirf naam, Score aur totals dikhte hain; kisi ke jawab ya phone number kabhi nahi.</T>
    {/* "Har din mein yahi naam dhoondo": the name goes into Dhoondo and stays there while the day is changed. */}
    <VersusSheet you={you} them={versus} when={day ? `Day ${day.day} · ${istDate(day.date)}` : "Poori series"} maximum={a ? a.summary?.maximum : d.maximum} onClose={() => setVersus(null)}
      onFollow={() => { if (versus) { onFind(versus.name.slice(0, 20)); onPart("find"); } setVersus(null); }} />
  </>;
}

/**
 * Find any student of the day by name or Rank. The website does the search. What is typed is kept by the screen, so it
 * stays when the day is changed. With `you`, each student found says how many marks ahead of or behind you they are.
 */
function Find({ id, q, onQ, you, daily, onPick }: { id: string; q: string; onQ: (q: string) => void; you?: BoardRow | null; daily: boolean; onPick?: (r: BoardRow) => void }) {
  const term = q.trim();
  return <>
    {/* The search box wears the Dhoondo tab's sky blue, with the same gloss, glint and running edge. */}
    <Shine radius={radius.pill} ring={2} tones={LOOK.find.rest} edge={LOOK.find.edge} gloss={colors.custom_tabGloss} glint={colors.custom_tabGlint} band={26} part={34} face={styles.search}>
      <Icon name="magnify" size={18} color={colors.custom_tabInkSoft} />
      <TextInput testID="aits-board-search" value={q} onChangeText={t => onQ(t.slice(0, 20))} placeholder="Naam ya Rank likho" placeholderTextColor={colors.custom_tabInkSoft}
        accessibilityLabel="Leaderboard mein dhoondo" autoCorrect={false} returnKeyType="search" style={[styles.input, noOutline]} />
    </Shine>
    {term && daily && !/^\d+$/.test(term) ? <T testID="aits-board-find-days" size={12} color={colors.custom_eyebrow}>Upar se din badlo: “{term}” us din mein bhi dhoonda jayega. Ek naam kai students ka ho sakta hai.</T> : null}
    {term ? <Found key={term} id={id} term={term} you={you} onPick={onPick} />
      : <T testID="aits-board-find-hint" size={13} color={colors.muted}>Kisi bhi student ka naam ya Rank likho. Jaise: Arjun, ya 25.</T>}
  </>;
}

/** The answer for one search term. A new term starts a new look-up, so an older answer is never shown under it. */
function Found({ id, term, you, onPick }: { id: string; term: string; you?: BoardRow | null; onPick?: (r: BoardRow) => void }) {
  const d: Board | null = useBoard(id, term);
  if (!d) return <Skeleton h={60} style={styles.soft} />;
  if (d.state === "error") return <T testID="aits-board-find-error" size={13} color={colors.error}>Dhoondh nahi paaye. Internet dekh kar dobara likho.</T>;
  const found = d.found || [];
  return found.length ? <BoardRows testID="aits-board-found" rows={found} you={you} look={LOOK.find} onPick={onPick} />
    : <T testID="aits-board-none" size={13} color={colors.muted}>Is naam ya Rank ka koi student nahi mila.</T>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.surface },
  content: { padding: space.lg, paddingTop: space.xs, gap: space.md },
  soft: { borderRadius: 22 }, round: { borderRadius: radius.pill },
  caps: { letterSpacing: 1.6, marginTop: space.xs },
  // 48 high as before: 44 inside the 2-point running edge.
  search: { flexDirection: "row", alignItems: "center", gap: 8, minHeight: 44, paddingHorizontal: space.md },
  // `position`: on the web a text box is the one piece that is not layered by itself, so the face's colours would be drawn over what is typed.
  input: { position: "relative", flex: 1, minHeight: 42, fontFamily: fonts.medium, fontSize: 14, color: colors.custom_tabInk, paddingVertical: 0 },
});
