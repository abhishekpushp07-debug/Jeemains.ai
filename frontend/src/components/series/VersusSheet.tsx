// "Aap vs <student>": one student's totals next to yours, for the leaderboard that is open (one day's, or the whole
// series'). It shows only what the two leaderboard rows already carry, so nothing more is asked from the website.
// One day at a time on purpose: the website gives a student a different handle on every day's leaderboard (seen for real
// on 24 Nov 2026), so the phone cannot follow one student from day to day without guessing by name. For a student with
// a name of their own the sheet offers "Har din mein yahi naam dhoondo": the name goes into Dhoondo and stays there while
// the student changes the day, and the student sees who carries that name each day. A student without a name is shown
// under a different "Learner XXXXXXXX" every day, so there is nothing to look for. The real day-by-day table needs the
// website (memory/WEBSITE_SERIES_RANK_NOTE.md, part 3).
import React from "react";
import { StyleSheet, View } from "react-native";
import { T } from "@/src/components/ui";
import { DSheet, Pill } from "@/src/components/design";
import { mmss, pc, r1 } from "@/src/analysis/format";
import { colors, space } from "@/src/theme";
import { BoardRow, grouped } from "./Board";

// What is compared, yours, theirs, and who is ahead on it: 1 = you, -1 = them, 0 = level, or not a race.
type Line = [string, string, string, number];

/**
 * `when` = which leaderboard the two rows are from, in words ("Day 5 · 13 Dec", "Poori series").
 * `onFollow` (a day's leaderboard, a student with a name of their own): puts that name into Dhoondo, where it stays while
 * the day is changed, so the same name can be looked at day after day. The student judges who it is; the phone does not.
 */
export function VersusSheet({ you, them, when, maximum, onClose, onFollow }: { you?: BoardRow | null; them: BoardRow | null; when: string; maximum?: number; onClose: () => void; onFollow?: () => void }) {
  if (!you || !them) return null;
  const whole = you.days != null; // the whole series: days handed in instead of one paper's time
  const gap = r1(you.score - them.score);
  const score = (r: BoardRow) => (maximum ? `${grouped(r.score)}/${grouped(maximum)}` : grouped(r.score));
  const lines: Line[] = [
    ["Rank", "#" + grouped(you.rank), "#" + grouped(them.rank), Math.sign(them.rank - you.rank)],
    ["Score", score(you), score(them), Math.sign(gap)],
    ["Accuracy", pc(you.accuracy), pc(them.accuracy), you.accuracy != null && them.accuracy != null ? Math.sign(you.accuracy - them.accuracy) : 0],
    ["Attempted", grouped(you.attempted), grouped(them.attempted), 0],
    whole ? ["Din diye", String(you.days), them.days != null ? String(them.days) : "—", 0] : ["Time", mmss(you.time), mmss(them.time), 0],
  ];
  return <DSheet visible onClose={onClose} testID="aits-versus-sheet" title={`Aap vs ${them.name}`}>
    <T testID="aits-versus-when" w="heavy" size={11} color={colors.custom_eyebrow} style={styles.caps}>{when.toUpperCase()}</T>
    <T testID="aits-versus-gap" w="bold" size={14} color={colors.custom_softText}>
      {gap > 0 ? `Aap ${them.name} se ${gap} marks aage ho.` : gap < 0 ? `${them.name} aapse ${-gap} marks aage hai.` : `Aap aur ${them.name} barabar ho.`}
    </T>
    <View testID="aits-versus-table" style={styles.table}>
      <View style={styles.row}>
        <View style={styles.what} />
        <T w="heavy" size={12} color={colors.custom_eyebrow} style={styles.cell}>AAP</T>
        <T w="heavy" size={12} color={colors.custom_eyebrow} numberOfLines={1} style={styles.cell}>{them.name.toUpperCase()}</T>
      </View>
      {lines.map(([what, mine, theirs, ahead]) => <View key={what} testID={"aits-versus-" + what.toLowerCase().replace(" ", "-")} style={[styles.row, styles.line]}>
        <T size={13} color={colors.muted} style={styles.what}>{what}</T>
        <T w={ahead > 0 ? "heavy" : "semibold"} size={16} color={ahead > 0 ? colors.custom_royalMid : colors.onSurface} numberOfLines={1} style={styles.cell}>{mine}</T>
        <T w={ahead < 0 ? "heavy" : "semibold"} size={16} color={ahead < 0 ? colors.custom_royalMid : colors.onSurface} numberOfLines={1} style={styles.cell}>{theirs}</T>
      </View>)}
    </View>
    <T testID="aits-versus-note" size={11.5} color={colors.custom_eyebrow}>
      Yeh sirf leaderboard ke totals hain; kisi ke jawab kabhi nahi dikhte.{whole ? "" : them.named ? "" : " Is student ne apna naam nahi rakha hai, isliye ise doosre din mein dhoonda nahi ja sakta."}
    </T>
    {onFollow && !whole && them.named ? <Pill testID="aits-versus-follow" icon="magnify" label="Har din mein yahi naam dhoondo" onPress={onFollow} /> : null}
    <Pill testID="aits-versus-close" kind="outline" label="Theek hai" onPress={onClose} />
  </DSheet>;
}

const styles = StyleSheet.create({
  caps: { letterSpacing: 1.6 },
  table: { borderRadius: 18, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_cardRaised, paddingHorizontal: space.md, paddingVertical: space.xs },
  row: { flexDirection: "row", alignItems: "center", gap: space.sm, minHeight: 40 },
  line: { borderTopWidth: 1, borderTopColor: colors.custom_cardLine },
  what: { flex: 1.1, minWidth: 0 },
  cell: { flex: 1, minWidth: 0, textAlign: "center" },
});
