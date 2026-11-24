// The pieces of the AITS Leaderboard: the way in from the series page, your own Rank card for the chosen day, the top
// three on their stage, the list rows and the notice card. Names, Scores and totals only, exactly as the website sends them.
// Every card here is glossy, with a glass glint crossing it and three colours running round its edge: the Rank card is the
// series page's baby pink streak card, the stage and the way in are Home's All India card (both looks live in ./looks).
import React, { useState, useSyncExternalStore } from "react";
import { StyleSheet, View, useWindowDimensions } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Icon, IconName, Press, T } from "@/src/components/ui";
import { Shine } from "@/src/analysis/Shine";
import { TabLook } from "@/src/components/GlossTabs";
import { mmss, pc, r1 } from "@/src/analysis/format";
import { Medal, MedalWash } from "@/src/rank/Medal";
import { SERIF } from "@/src/rank/tones";
import { colors, pastel, pastelEdges, space } from "@/src/theme";
import { SeriesBackdrop, onyxShine, pinkShine } from "./looks";

export type BoardRow = { rank: number; name: string; named: boolean; handle: string; score: number; attempted: number; accuracy: number | null; time: number; is_you: boolean };
export type Board = { state: string; n: number; title?: string; rows: BoardRow[]; around: BoardRow[]; found: BoardRow[]; you?: BoardRow | null };

export const grouped = (n: number) => n.toLocaleString("en-IN");
const nameOf = (r: BoardRow) => (r.is_you ? (r.named ? `Aap · ${r.name}` : "Aap") : r.name);

// A notice wears the series' "upcoming" teal into sky, like an upcoming day's card.
const UPCOMING = [pastel.upcoming.from, pastel.upcoming.to] as const;

// The slice of the page that is on screen, top and bottom, in steps of 120 points. A row outside it rests its shine, so a
// long list costs no more than the rows in view. The screen says where it is on every scroll.
const STEP = 120;
let seen: readonly [number, number] = [0, 1200];
const watchers = new Set<() => void>();
const watch = (f: () => void) => { watchers.add(f); return () => { watchers.delete(f); }; };
const seenNow = () => seen;
/** The screen's scroll position: `top` = how far the page is scrolled, `height` = how much of it shows. */
export function pageSeen(top: number, height: number) {
  const from = Math.floor(top / STEP) * STEP, to = Math.ceil((top + height) / STEP) * STEP;
  if (from === seen[0] && to === seen[1]) return;
  seen = [from, to];
  watchers.forEach(f => f());
}
// Gold, silver, bronze: light, middle, deep and the ink that reads on them.
const METAL = [
  [colors.custom_medalGoldLight, colors.custom_medalGold, colors.custom_medalGoldDeep, colors.custom_medalGoldInk],
  [colors.custom_medalSilverLight, colors.custom_medalSilver, colors.custom_medalSilverDeep, colors.custom_medalSilverInk],
  [colors.custom_medalBronzeLight, colors.custom_medalBronze, colors.custom_medalBronzeDeep, colors.custom_medalBronzeInk],
] as const;
const STEP_HEIGHT = [96, 74, 60];

/** The way in from the series page: Home's All India card as a bar, with a gold cup. */
export function BoardLink({ onPress }: { onPress: () => void }) {
  return <Press testID="series-open-leaderboard" onPress={onPress} accessibilityLabel="AITS Leaderboard. Har din ke Toppers aur aapka All India Rank" scaleTo={0.98} style={styles.link}>
    <Shine radius={20} {...onyxShine} band={72} backdrop={<SeriesBackdrop />} face={styles.linkFace}>
      <View style={styles.cup}><Icon name="trophy" size={22} color={colors.custom_medalGoldInk} /></View>
      <View style={styles.grow}>
        <T w="heavy" size={16} color={colors.onSurfaceInverse}>AITS Leaderboard</T>
        <T size={12} color={colors.custom_whiteA70} numberOfLines={1}>Har din ke Toppers · aapka All India Rank</T>
      </View>
      <Icon name="chevron-right" size={22} color={colors.onSurfaceInverse} />
    </Shine>
  </Press>;
}

/** Your own place on the chosen day, on the series page's baby pink streak card: the Rank in the Rank Card's serif, then Score, Attempted, Accuracy and time. */
export function YouCard({ kicker, you, n, maximum, live }: { kicker: string; you?: BoardRow | null; n: number; maximum?: number; live: boolean }) {
  const ink = colors.custom_seriesPinkInk; // the small words on baby pink
  const narrow = useWindowDimensions().width < 360; // a small phone: the four facts sit two by two, so no number is cut
  const facts: [string, string][] = you ? [["Score", maximum ? `${you.score}/${maximum}` : String(you.score)], ["Attempted", String(you.attempted)], ["Accuracy", pc(you.accuracy)], ["Time", mmss(you.time)]] : [];
  return <View testID="aits-board-you">
    <Shine radius={24} {...pinkShine} face={styles.you}>
      <View style={styles.kickers}>
        <T w="heavy" size={10} color={ink} style={styles.caps}>{kicker}</T>
        <T testID="aits-board-count" w="heavy" size={10} color={ink} style={styles.caps}>{grouped(n)} {n === 1 ? "STUDENT" : "STUDENTS"}</T>
      </View>
      {you ? <>
        <View style={styles.rankRow}>
          {you.rank <= 3 ? <Medal n={you.rank} /> : null}
          <T testID="aits-board-you-rank" color={colors.custom_pastelInk} style={styles.rank}>#{grouped(you.rank)}</T>
          <View style={styles.grow}>
            {/* Only the live day is the All India race; a missed day done later from the archive is ranked on that paper's own board. */}
            <T testID="aits-board-you-label" w="heavy" size={14} color={colors.custom_pastelInk}>{live ? "Aapka All India Rank" : "Is paper mein aapka Rank"}</T>
            <T testID="aits-board-you-name" size={12} color={ink} numberOfLines={2}>Leaderboard par naam: {you.name}</T>
          </View>
        </View>
        <View style={styles.facts}>
          {facts.map(([label, value], i) => <View key={label} style={[styles.fact, narrow && styles.factHalf, (narrow ? i % 2 === 1 : i > 0) && styles.factLine]}>
            <T w="heavy" size={15} color={colors.custom_pastelInk} numberOfLines={1}>{value}</T>
            <T size={10.5} color={ink} numberOfLines={1}>{label}</T>
          </View>)}
        </View>
      </> : <T testID="aits-board-you-none" w="bold" size={13} color={ink}>Is din ke leaderboard mein aapka Rank nahi hai.</T>}
    </Shine>
  </View>;
}

function Step({ row, place, narrow }: { row?: BoardRow; place: 1 | 2 | 3; narrow: boolean }) {
  const [light, mid, deep, ink] = METAL[place - 1];
  return <View testID={`aits-board-podium-${place}`} style={[styles.step, !row && styles.vacant]} accessibilityLabel={row ? `Rank ${row.rank}, ${nameOf(row)}, Score ${row.score}, Accuracy ${pc(row.accuracy)}` : `Rank ${place} abhi khaali hai`}>
    {place === 1 ? <Icon name="crown" size={24} color={mid} /> : null}
    <Medal n={row?.rank ?? place} />
    <T w="heavy" size={12.5} color={colors.onSurfaceInverse} numberOfLines={2} style={styles.center}>{row ? nameOf(row) : "—"}</T>
    <LinearGradient colors={[light, mid, deep]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.block, { height: STEP_HEIGHT[place - 1] }]}>
      <T color={ink} style={place === 1 ? styles.scoreBig : styles.score}>{row ? row.score : "—"}</T>
      {row ? <T w="bold" size={9.5} color={ink} numberOfLines={1}>{narrow ? "Acc." : "Accuracy"} {pc(row.accuracy)}</T> : null}
    </LinearGradient>
  </View>;
}

/** The first three of the day, second · first · third, standing on gold, silver and bronze on Home's All India card. An empty place waits, dimmed. */
export function Podium({ rows, title }: { rows: BoardRow[]; title?: string }) {
  const narrow = useWindowDimensions().width < 360;
  return <View testID="aits-board-podium">
    <Shine radius={28} {...onyxShine} backdrop={<SeriesBackdrop />} face={styles.stage}>
      <View style={styles.between}>
        <T w="heavy" size={10} color={colors.custom_medalGold} style={styles.caps}>TOP 3</T>
        {title ? <T size={11} color={colors.custom_whiteA70} numberOfLines={1} style={styles.stageTitle}>{title}</T> : null}
      </View>
      <View style={styles.podium}>
        <Step row={rows[1]} place={2} narrow={narrow} />
        <Step row={rows[0]} place={1} narrow={narrow} />
        <Step row={rows[2]} place={3} narrow={narrow} />
      </View>
    </Shine>
  </View>;
}

/**
 * List rows as glossy cards in the open part's own soft colours (`look`), with that part's three colours running round
 * each one; your own row is baby pink like your Rank card, with a thicker edge. A medal for the first three, "#rank"
 * after that. With `you`, every other row says how many marks it is ahead of or behind you.
 * Only the rows on screen move (see `pageSeen`); the glint reaches each row a little after the one above it.
 */
export function BoardRows({ rows, you, look, testID }: { rows: BoardRow[]; you?: BoardRow | null; look: TabLook; testID: string }) {
  const [box, setBox] = useState<{ y: number; h: number } | null>(null);
  const [from, to] = useSyncExternalStore(watch, seenNow, seenNow);
  const pitch = box && rows.length ? box.h / rows.length : 0;
  return <View testID={testID} style={styles.rows}
    onLayout={e => { const { y, height: h } = e.nativeEvent.layout; setBox(old => (old && Math.abs(old.y - y) < 1 && Math.abs(old.h - h) < 1 ? old : { y, h })); }}>
    {rows.map((r, i) => {
      const ahead = you && !r.is_you ? r1(r.score - you.score) : null;
      // Until the list is measured only the first dozen move; after that, the rows on screen and one step around them.
      const rest = box ? box.y + (i + 1) * pitch < from - STEP || box.y + i * pitch > to + STEP : i > 11;
      return <View key={r.handle} testID={`aits-board-row-${r.handle}`}>
        <Shine radius={16} ring={r.is_you ? 3 : 2} tones={r.is_you ? pinkShine.tones : look.rest} edge={r.is_you ? pinkShine.edge : look.edge}
          gloss={colors.custom_tabGloss} glint={colors.custom_tabGlint} band={34} part={34} delay={(i % 8) * 140} rest={rest} face={r.is_you ? styles.mine : styles.row}>
          <MedalWash n={r.rank} />
          {r.rank <= 3 ? <View style={styles.markBox}><Medal n={r.rank} /></View>
            : <T w="heavy" size={r.rank > 999 ? 12 : 14} color={colors.custom_tabInk} numberOfLines={1} style={styles.markText}>#{r.rank}</T>}
          <View style={styles.grow}>
            <T w="heavy" size={14.5} color={colors.custom_tabInk} numberOfLines={1}>{nameOf(r)}</T>
            <T size={11.5} color={colors.custom_tabInkSoft} numberOfLines={1}>Attempted {r.attempted} · Accuracy {pc(r.accuracy)} · {mmss(r.time)}</T>
          </View>
          <View style={styles.side}>
            <T w="heavy" size={18} color={colors.custom_tabInk}>{r.score}</T>
            {r.is_you ? <View style={styles.youTag}><T size={10} w="heavy" color={colors.custom_tabInk}>AAP</T></View>
              : ahead != null ? <T w="bold" size={10.5} color={colors.custom_tabInkSoft}>{ahead > 0 ? `${ahead} aage` : ahead < 0 ? `${-ahead} peeche` : "barabar"}</T> : null}
          </View>
        </Shine>
      </View>;
    })}
  </View>;
}

/** A notice (no paper yet, a result still sealed, a leaderboard not ready) in the colours of an upcoming day's card, with the same gloss, glint and running edge. */
export function NoticeCard({ testID, icon, title, note, noteTestID, children }: { testID: string; icon: IconName; title: string; note: string; noteTestID?: string; children?: React.ReactNode }) {
  const p = pastel.upcoming;
  return <View testID={testID}>
    <Shine radius={24} ring={2} tones={UPCOMING} edge={pastelEdges.upcoming} gloss={colors.custom_seriesPastelGloss} glint={colors.custom_seriesPastelGlint} band={72} part={46} corner face={styles.notice}>
      <Icon name={icon} size={24} color={p.ink} />
      <T w="heavy" size={16} color={colors.custom_pastelInk}>{title}</T>
      <T testID={noteTestID} size={13} color={p.body}>{note}</T>
      {children}
    </Shine>
  </View>;
}

const styles = StyleSheet.create({
  grow: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, caps: { letterSpacing: 1.6 },
  between: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: space.sm },
  // The day and the class size share a line; on a small phone the class size drops to the next line instead of cutting either.
  kickers: { flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between", columnGap: space.sm, rowGap: 2 },
  link: { borderRadius: 20 },
  linkFace: { flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 64, paddingHorizontal: 16, paddingVertical: 12, backgroundColor: colors.custom_series },
  cup: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_medalGold },
  // 19 inside the 2-point running edge, as on the streak card.
  you: { padding: 19, gap: space.md },
  rankRow: { flexDirection: "row", alignItems: "center", gap: space.md },
  rank: { fontFamily: SERIF, fontSize: 40, lineHeight: 46 },
  facts: { flexDirection: "row", flexWrap: "wrap", rowGap: 10, borderRadius: 16, backgroundColor: colors.custom_whiteA70, paddingVertical: 10 },
  fact: { flex: 1, minWidth: 0, alignItems: "center", gap: 1, paddingHorizontal: 4 },
  factHalf: { flexGrow: 0, flexShrink: 0, flexBasis: "50%" },
  factLine: { borderLeftWidth: 1, borderLeftColor: colors.custom_seriesPinkDeep },
  // 19 inside the edge, as on Home's card. No padding under the steps: they stand on the card's own bottom edge.
  stage: { paddingTop: 19, paddingHorizontal: 19, gap: space.md, backgroundColor: colors.custom_series },
  stageTitle: { flexShrink: 1, textAlign: "right" },
  podium: { flexDirection: "row", alignItems: "flex-end", gap: 8 },
  step: { flex: 1, minWidth: 0, alignItems: "center", gap: 5 },
  vacant: { opacity: 0.4 },
  block: { alignSelf: "stretch", borderTopLeftRadius: 14, borderTopRightRadius: 14, alignItems: "center", justifyContent: "center", gap: 1, paddingHorizontal: 4 },
  score: { fontFamily: SERIF, fontSize: 22, lineHeight: 26 },
  scoreBig: { fontFamily: SERIF, fontSize: 28, lineHeight: 32 },
  rows: { gap: 8 },
  // A row is 60 high as before: 56 inside its 2-point edge, or 54 inside your own row's 3-point edge.
  row: { flexDirection: "row", alignItems: "center", gap: space.sm, minHeight: 56, paddingVertical: 8, paddingLeft: 4, paddingRight: space.md - 2 },
  mine: { flexDirection: "row", alignItems: "center", gap: space.sm, minHeight: 54, paddingVertical: 7, paddingLeft: 3, paddingRight: space.md - 3 },
  markBox: { width: 48, alignItems: "center" },
  markText: { width: 48, textAlign: "center" },
  side: { alignItems: "flex-end", gap: 2 },
  youTag: { height: 20, paddingHorizontal: 8, borderRadius: 10, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_tabChip },
  notice: { padding: 18, gap: space.sm },
});
