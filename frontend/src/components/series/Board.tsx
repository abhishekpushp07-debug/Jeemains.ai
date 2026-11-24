// The pieces of the AITS Leaderboard: the way in from the series page, your own Rank card for the chosen day, the top
// three on their onyx-and-ruby stage, and the list rows. Names, Scores and totals only, exactly as the website sends them.
import React from "react";
import { StyleSheet, View, useWindowDimensions } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Icon, Press, T } from "@/src/components/ui";
import { Shine } from "@/src/analysis/Shine";
import { TONE, mmss, pc, r1 } from "@/src/analysis/format";
import { Medal, MedalWash } from "@/src/rank/Medal";
import { SERIF } from "@/src/rank/tones";
import { colors, pastel, pastelEdges, seriesEdge, space } from "@/src/theme";

export type BoardRow = { rank: number; name: string; named: boolean; handle: string; score: number; attempted: number; accuracy: number | null; time: number; is_you: boolean };
export type Board = { state: string; n: number; title?: string; rows: BoardRow[]; around: BoardRow[]; found: BoardRow[]; you?: BoardRow | null };

export const grouped = (n: number) => n.toLocaleString("en-IN");
const nameOf = (r: BoardRow) => (r.is_you ? (r.named ? `Aap · ${r.name}` : "Aap") : r.name);

// The Home series card's own colours (onyx into ruby), drawn once.
const STAGE = <LinearGradient pointerEvents="none" colors={[colors.custom_seriesFrom, colors.custom_seriesMid, colors.custom_seriesTo]} locations={[0, 0.55, 1]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />;
const DONE = [pastel.done.from, pastel.done.to] as const;
// Gold, silver, bronze: light, middle, deep and the ink that reads on them.
const METAL = [
  [colors.custom_medalGoldLight, colors.custom_medalGold, colors.custom_medalGoldDeep, colors.custom_medalGoldInk],
  [colors.custom_medalSilverLight, colors.custom_medalSilver, colors.custom_medalSilverDeep, colors.custom_medalSilverInk],
  [colors.custom_medalBronzeLight, colors.custom_medalBronze, colors.custom_medalBronzeDeep, colors.custom_medalBronzeInk],
] as const;
const STEP_HEIGHT = [96, 74, 60];

/** The way in from the series page: a glossy onyx-and-ruby bar with a gold cup. */
export function BoardLink({ onPress }: { onPress: () => void }) {
  return <Press testID="series-open-leaderboard" onPress={onPress} accessibilityLabel="AITS Leaderboard. Har din ke Toppers aur aapka All India Rank" scaleTo={0.98} style={styles.link}>
    <Shine radius={20} ring={2} backdrop={STAGE} edge={seriesEdge} gloss={colors.custom_seriesGloss} glint={colors.custom_seriesGlint} band={72} part={46} corner face={styles.linkFace}>
      <View style={styles.cup}><Icon name="trophy" size={22} color={colors.custom_medalGoldInk} /></View>
      <View style={styles.grow}>
        <T w="heavy" size={16} color={colors.onSurfaceInverse}>AITS Leaderboard</T>
        <T size={12} color={colors.custom_whiteA70} numberOfLines={1}>Har din ke Toppers · aapka All India Rank</T>
      </View>
      <Icon name="chevron-right" size={22} color={colors.onSurfaceInverse} />
    </Shine>
  </Press>;
}

/** Your own place on the chosen day: the Rank in the Rank Card's serif, then Score, Attempted, Accuracy and time. */
export function YouCard({ kicker, you, n, maximum, live }: { kicker: string; you?: BoardRow | null; n: number; maximum?: number; live: boolean }) {
  const p = pastel.done;
  const narrow = useWindowDimensions().width < 360; // a small phone: the four facts sit two by two, so no number is cut
  const facts: [string, string][] = you ? [["Score", maximum ? `${you.score}/${maximum}` : String(you.score)], ["Attempted", String(you.attempted)], ["Accuracy", pc(you.accuracy)], ["Time", mmss(you.time)]] : [];
  return <View testID="aits-board-you">
    <Shine radius={24} ring={2} tones={DONE} edge={pastelEdges.done} gloss={colors.custom_seriesPastelGloss} glint={colors.custom_seriesPastelGlint} band={72} part={46} corner face={styles.you}>
      <View style={styles.kickers}>
        <T w="heavy" size={10} color={p.ink} style={styles.caps}>{kicker}</T>
        <T testID="aits-board-count" w="heavy" size={10} color={p.ink} style={styles.caps}>{grouped(n)} {n === 1 ? "STUDENT" : "STUDENTS"}</T>
      </View>
      {you ? <>
        <View style={styles.rankRow}>
          {you.rank <= 3 ? <Medal n={you.rank} /> : null}
          <T testID="aits-board-you-rank" color={colors.custom_pastelInk} style={styles.rank}>#{grouped(you.rank)}</T>
          <View style={styles.grow}>
            {/* Only the live day is the All India race; a missed day done later from the archive is ranked on that paper's own board. */}
            <T testID="aits-board-you-label" w="heavy" size={14} color={colors.custom_pastelInk}>{live ? "Aapka All India Rank" : "Is paper mein aapka Rank"}</T>
            <T testID="aits-board-you-name" size={12} color={p.body} numberOfLines={2}>Leaderboard par naam: {you.name}</T>
          </View>
        </View>
        <View style={styles.facts}>
          {facts.map(([label, value], i) => <View key={label} style={[styles.fact, narrow && styles.factHalf, (narrow ? i % 2 === 1 : i > 0) && styles.factLine]}>
            <T w="heavy" size={15} color={colors.custom_pastelInk} numberOfLines={1}>{value}</T>
            <T size={10.5} color={p.body} numberOfLines={1}>{label}</T>
          </View>)}
        </View>
      </> : <T testID="aits-board-you-none" w="bold" size={13} color={p.body}>Is din ke leaderboard mein aapka Rank nahi hai.</T>}
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

/** The first three of the day, second · first · third, standing on gold, silver and bronze. An empty place waits, dimmed. */
export function Podium({ rows, title }: { rows: BoardRow[]; title?: string }) {
  const narrow = useWindowDimensions().width < 360;
  return <View testID="aits-board-podium">
    <Shine radius={24} ring={2} backdrop={STAGE} edge={seriesEdge} gloss={colors.custom_seriesGloss} glint={colors.custom_seriesGlint} band={96} part={46} corner face={styles.stage}>
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

/** List rows: a medal for the first three, "#rank" after that. With `you`, every other row says how many marks it is ahead of or behind you. */
export function BoardRows({ rows, you, testID }: { rows: BoardRow[]; you?: BoardRow | null; testID: string }) {
  return <View testID={testID} style={styles.rows}>
    {rows.map(r => {
      const ahead = you && !r.is_you ? r1(r.score - you.score) : null;
      return <View key={r.handle} testID={`aits-board-row-${r.handle}`} style={[styles.row, r.is_you && styles.mine]}>
        <MedalWash n={r.rank} />
        {r.rank <= 3 ? <View style={styles.markBox}><Medal n={r.rank} /></View>
          : <T w="heavy" size={r.rank > 999 ? 12 : 14} numberOfLines={1} style={styles.markText}>#{r.rank}</T>}
        <View style={styles.grow}>
          <T w="heavy" size={14.5} numberOfLines={1}>{nameOf(r)}</T>
          <T size={11.5} color={colors.muted} numberOfLines={1}>Attempted {r.attempted} · Accuracy {pc(r.accuracy)} · {mmss(r.time)}</T>
        </View>
        <View style={styles.side}>
          <T w="heavy" size={18}>{r.score}</T>
          {r.is_you ? <View style={styles.youTag}><T size={10} w="heavy" color={colors.brandText}>AAP</T></View>
            : ahead != null ? <T w="bold" size={10.5} color={colors.muted}>{ahead > 0 ? `${ahead} aage` : ahead < 0 ? `${-ahead} peeche` : "barabar"}</T> : null}
        </View>
      </View>;
    })}
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
  // 18 inside the 2-point running edge, as on the big day cards.
  you: { padding: 18, gap: space.md },
  rankRow: { flexDirection: "row", alignItems: "center", gap: space.md },
  rank: { fontFamily: SERIF, fontSize: 40, lineHeight: 46 },
  facts: { flexDirection: "row", flexWrap: "wrap", rowGap: 10, borderRadius: 16, backgroundColor: colors.custom_whiteA70, paddingVertical: 10 },
  fact: { flex: 1, minWidth: 0, alignItems: "center", gap: 1, paddingHorizontal: 4 },
  factHalf: { flexGrow: 0, flexShrink: 0, flexBasis: "50%" },
  factLine: { borderLeftWidth: 1, borderLeftColor: colors.custom_doneTo },
  // No padding under the steps: they stand on the card's own bottom edge.
  stage: { paddingTop: 16, paddingHorizontal: 16, gap: space.md, backgroundColor: colors.custom_series },
  stageTitle: { flexShrink: 1, textAlign: "right" },
  podium: { flexDirection: "row", alignItems: "flex-end", gap: 8 },
  step: { flex: 1, minWidth: 0, alignItems: "center", gap: 5 },
  vacant: { opacity: 0.4 },
  block: { alignSelf: "stretch", borderTopLeftRadius: 14, borderTopRightRadius: 14, alignItems: "center", justifyContent: "center", gap: 1, paddingHorizontal: 4 },
  score: { fontFamily: SERIF, fontSize: 22, lineHeight: 26 },
  scoreBig: { fontFamily: SERIF, fontSize: 28, lineHeight: 32 },
  rows: { gap: 8 },
  row: { flexDirection: "row", alignItems: "center", gap: space.sm, minHeight: 60, paddingVertical: 10, paddingLeft: 6, paddingRight: space.md, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card, overflow: "hidden" },
  mine: { borderColor: TONE.brand.line, backgroundColor: TONE.brand.soft },
  markBox: { width: 48, alignItems: "center" },
  markText: { width: 48, textAlign: "center" },
  side: { alignItems: "flex-end", gap: 2 },
  youTag: { height: 20, paddingHorizontal: 8, borderRadius: 10, borderWidth: 1, borderColor: TONE.brand.line, alignItems: "center", justifyContent: "center" },
});
