// The Rank Share Card: a 4 : 5 picture of the student's Rank and Score for one All India day (or the whole series), in the
// colours of Home's All India card, with the student's own message written on it. It is drawn in units of its own width,
// so its photo looks the same from every phone. Nothing on it moves: a photo of a moving card would catch it mid-shine.
import React from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Icon, T } from "@/src/components/ui";
import { SERIF } from "@/src/rank/tones";
import { colors, seriesEdge } from "@/src/theme";
import { grouped } from "./Board";
import { SeriesBackdrop } from "./looks";

/** `when` = the day in words (for the message); `kicker` = the same in capitals (for the card); `stats` = three label + value pairs; `name` = the leaderboard name, if one is written. */
export type RankFacts = { when: string; kicker: string; label: string; rank: number; n: number; stats: [string, string][]; name?: string };

export const MESSAGE_MAX = 80;

/** What goes out with the picture: the student's message first, then the Rank in words and the student's own link. */
export function rankCaption(f: RankFacts, message: string, link: string) {
  const own = message.trim();
  return [...(own ? [own, ""] : []),
    `🏆 JEELIVE.AI All India Test Series · ${f.when}`,
    `${f.label}: #${grouped(f.rank)} (${grouped(f.n)} students mein)`,
    f.stats.map(([label, value]) => `${label} ${value}`).join(" · "),
    "",
    `Tum bhi roz ka All India mock do 👉 ${link}`].join("\n");
}

// The card's words never follow the phone's text-size setting: the picture must come out the same for everyone.
const C = (p: React.ComponentProps<typeof T>) => <T allowFontScaling={false} {...p} />;

export function RankCard({ f, message, width }: { f: RankFacts; message: string; width: number }) {
  const u = width / 320;
  const rank = "#" + grouped(f.rank);
  const big = (rank.length <= 4 ? 78 : rank.length <= 6 ? 64 : rank.length <= 7 ? 54 : 44) * u; // a long Rank is written smaller, never cut
  const own = message.trim();
  return <View style={[styles.card, { width, height: width * 1.25, borderRadius: 26 * u }]}>
    {/* Home's ruby, gold and rose as a still frame. */}
    <LinearGradient colors={seriesEdge} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    <View style={[styles.face, { margin: 3 * u, borderRadius: 23 * u, paddingHorizontal: 18 * u, paddingVertical: 16 * u }]}>
      <SeriesBackdrop />
      <View style={{ gap: 3 * u }}>
        <View style={styles.between}>
          <C w="heavy" size={12 * u} color={colors.custom_medalGold} style={{ letterSpacing: 2.2 * u }}>JEELIVE.AI</C>
          <C w="bold" size={8.5 * u} color={colors.custom_whiteA70} style={{ letterSpacing: 1.4 * u }}>ALL INDIA TEST SERIES</C>
        </View>
        <C w="heavy" size={9.5 * u} color={colors.onSurfaceInverse} style={{ letterSpacing: 1.6 * u }}>{f.kicker}</C>
      </View>
      <View style={[styles.middle, { gap: 2 * u }]}>
        <View style={[styles.cup, { width: 34 * u, height: 34 * u, borderRadius: 17 * u }]}>
          <Icon name={f.rank <= 3 ? "crown" : "trophy"} size={19 * u} color={colors.custom_medalGoldInk} />
        </View>
        <C color={colors.custom_medalGoldLight} style={{ fontFamily: SERIF, fontSize: big, lineHeight: big * 1.12 }}>{rank}</C>
        <C w="heavy" size={12.5 * u} color={colors.onSurfaceInverse} style={{ letterSpacing: 2.4 * u }}>{f.label.toUpperCase()}</C>
        <C size={11 * u} color={colors.custom_whiteA70}>{grouped(f.n)} {f.n === 1 ? "student" : "students"} mein</C>
      </View>
      <View style={[styles.stats, { gap: 7 * u }]}>
        {f.stats.map(([label, value]) => <View key={label} style={[styles.stat, { borderRadius: 13 * u, paddingVertical: 7 * u, paddingHorizontal: 3 * u }]}>
          <C w="heavy" size={(value.length > 8 ? 12.5 : 15.5) * u} color={colors.onSurfaceInverse} numberOfLines={1}>{value}</C>
          <C size={9 * u} color={colors.custom_whiteA70} numberOfLines={1}>{label}</C>
        </View>)}
      </View>
      {own || f.name ? <View style={[styles.quote, { borderLeftWidth: 2.5 * u, paddingLeft: 10 * u, gap: 3 * u }]}>
        {own ? <C color={colors.onSurfaceInverse} numberOfLines={3} style={{ fontFamily: SERIF, fontStyle: "italic", fontSize: 13 * u, lineHeight: 18 * u }}>“{own}”</C> : null}
        {f.name ? <C w="heavy" size={10.5 * u} color={colors.custom_medalGold} numberOfLines={1}>— {f.name}</C> : null}
      </View> : null}
      <View style={styles.between}>
        <C w="heavy" size={11.5 * u} color={colors.onSurfaceInverse}>jeelive.ai</C>
        <C w="bold" size={8.5 * u} color={colors.custom_medalGold} style={{ letterSpacing: 1.6 * u }}>SCORE 200+ WITH AI</C>
      </View>
    </View>
  </View>;
}

const styles = StyleSheet.create({
  card: { overflow: "hidden", backgroundColor: colors.custom_series },
  face: { flex: 1, overflow: "hidden", justifyContent: "space-between", backgroundColor: colors.custom_series },
  between: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  middle: { alignItems: "center" },
  cup: { alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_medalGold },
  stats: { flexDirection: "row" },
  stat: { flex: 1, minWidth: 0, alignItems: "center", backgroundColor: colors.custom_seriesGloss, borderWidth: 1, borderColor: colors.custom_seriesSheen },
  quote: { borderLeftColor: colors.custom_medalGold },
});
