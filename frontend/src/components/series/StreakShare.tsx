// The Streak share picture: the All India streak the way chat apps show one, a flame with the number of days in a row,
// in fire colours (amber into hot orange into red into ember), with the last seven days, three totals and the student's
// own message. 4 : 5 and drawn in units of its own width, like the Rank share picture, so its photo is the same from every
// phone. Nothing on it moves. Every number is the website's own streak; the phone only lays it out.
import React, { useId } from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Svg, { Defs, RadialGradient, Rect, Stop } from "react-native-svg";
import { Icon, T } from "@/src/components/ui";
import { SERIF } from "@/src/rank/tones";
import { colors, fireEdge } from "@/src/theme";
import { DayInfo, Streak } from "@/src/series";

type Mark = "done" | "missed" | "today" | "ahead";
/** `count` = days in a row now; `best` = the longest run; `done` of `total` days handed in; `week` = the last seven series days up to today. */
export type StreakFacts = { count: number; best: number; done: number; total: number; cups: number; cupsOf: number; week: { day: number; mark: Mark }[] };

export function streakFacts(s: Streak, days: DayInfo[]): StreakFacts {
  const cups = s.milestones || [];
  const today = days.findIndex(d => d.isToday);
  const end = today >= 0 ? today : days.filter(d => d.tone !== "upcoming").length - 1; // after the series: its last day
  const week = end < 0 ? [] : days.slice(Math.max(0, end - 6), end + 1)
    .map(d => ({ day: d.day, mark: (d.tone === "done" ? "done" : d.tone === "missed" ? "missed" : d.tone === "today" ? "today" : "ahead") as Mark }));
  return { count: s.current_streak, best: s.best_streak, done: s.completed_count, total: s.total_days || days.length, cups: cups.filter(c => c.earned).length, cupsOf: cups.length, week };
}

/** What goes out with the picture: the student's message first, then the streak in words and the student's own link. */
export function streakCaption(f: StreakFacts, message: string, link: string) {
  const own = message.trim();
  return [...(own ? [own, ""] : []),
    "🔥 JEELIVE.AI All India Test Series",
    f.count ? `Meri streak: ${f.count} din lagataar` : `Meri best streak: ${f.best} din`,
    `${f.done}/${f.total} din poore · Best streak ${f.best} din`,
    "",
    `Tum bhi roz ka All India mock do 👉 ${link}`].join("\n");
}

// The card's words never follow the phone's text-size setting: the picture must come out the same for everyone.
const C = (p: React.ComponentProps<typeof T>) => <T allowFontScaling={false} {...p} />;
const FIRE = [colors.custom_fireAmber, colors.custom_fireOrange, colors.custom_fireRed, colors.custom_fireEmber] as const;
const DOT = { done: ["fire", colors.custom_fireOrange], today: ["timer-sand", colors.custom_fireInk], missed: ["close", colors.custom_fireCream], ahead: ["circle-small", colors.custom_fireCream] } as const;

export function StreakCard({ f, message, width }: { f: StreakFacts; message: string; width: number }) {
  const glow = "fireGlow" + useId().replace(/[^a-z0-9]/gi, "");
  const u = width / 320;
  const running = f.count > 0, n = running ? f.count : f.best; // no run today: the longest one stands on the card
  const big = (String(n).length <= 2 ? 104 : 78) * u;
  const own = message.trim();
  const stats: [string, string][] = [["Din poore", `${f.done}/${f.total}`], ["Best streak", `${f.best} din`], ...(f.cupsOf ? [["Cups", `${f.cups}/${f.cupsOf}`] as [string, string]] : [])];
  return <View style={[styles.card, { width, height: width * 1.25, borderRadius: 26 * u }]}>
    <LinearGradient colors={fireEdge} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    <View style={[styles.face, { margin: 3 * u, borderRadius: 23 * u, paddingHorizontal: 18 * u, paddingVertical: 16 * u }]}>
      <LinearGradient colors={FIRE} locations={[0, 0.2, 0.52, 1]} style={StyleSheet.absoluteFill} />
      {/* The hot heart of the fire behind the flame. Explicit stopOpacity: native SVG ignores alpha inside stopColor.
          Sizes in numbers (the face is the card less its 3-unit frame), the way the arena's background is drawn. */}
      <Svg style={StyleSheet.absoluteFill} width={width - 6 * u} height={width * 1.25 - 6 * u} pointerEvents="none">
        <Defs>
          <RadialGradient id={glow} cx="34%" cy="30%" rx="46%" ry="30%">
            <Stop offset="0" stopColor={colors.custom_fireCream} stopOpacity={0.55} />
            <Stop offset="1" stopColor={colors.custom_fireCream} stopOpacity={0} />
          </RadialGradient>
        </Defs>
        <Rect x={0} y={0} width={width - 6 * u} height={width * 1.25 - 6 * u} fill={`url(#${glow})`} />
      </Svg>
      <View style={styles.between}>
        <C w="heavy" size={12 * u} color={colors.custom_fireInk} style={{ letterSpacing: 2.2 * u }}>JEELIVE.AI</C>
        <C w="bold" size={8.5 * u} color={colors.custom_fireInk} style={{ letterSpacing: 1.4 * u }}>ALL INDIA TEST SERIES</C>
      </View>
      <View style={styles.middle}>
        <View style={[styles.hero, { gap: 2 * u }]}>
          <Icon name="fire" size={96 * u} color={colors.custom_fireCream} />
          <C w="heavy" size={big} color={colors.onSurfaceInverse} style={{ lineHeight: big * 1.04, textShadowColor: colors.custom_fireShade, textShadowOffset: { width: 0, height: 3 * u }, textShadowRadius: 8 * u }}>{n}</C>
        </View>
        <C w="heavy" size={13 * u} color={colors.onSurfaceInverse} style={{ letterSpacing: 3 * u }}>{running ? "DIN KI STREAK" : "BEST STREAK"}</C>
        <C size={11 * u} color={colors.custom_fireCream}>{running ? "lagataar, bina ek din chhode" : "ab phir se aag lagani hai"}</C>
      </View>
      {f.week.length ? <View style={[styles.week, { gap: 7 * u }]}>
        {f.week.map(d => <View key={d.day} style={[styles.weekDay, { gap: 2 * u }]}>
          <View style={[styles.dot, { width: 26 * u, height: 26 * u, borderRadius: 13 * u, borderWidth: 1.5 * u }, d.mark === "done" ? styles.dotDone : d.mark === "today" ? styles.dotToday : styles.dotOff]}>
            <Icon name={DOT[d.mark][0]} size={(d.mark === "done" ? 17 : 13) * u} color={DOT[d.mark][1]} />
          </View>
          <C w="bold" size={8.5 * u} color={colors.custom_fireCream}>D{d.day}</C>
        </View>)}
      </View> : null}
      <View style={[styles.stats, { gap: 7 * u }]}>
        {stats.map(([label, value]) => <View key={label} style={[styles.stat, { borderRadius: 13 * u, paddingVertical: 6 * u, paddingHorizontal: 3 * u }]}>
          <C w="heavy" size={15 * u} color={colors.onSurfaceInverse} numberOfLines={1}>{value}</C>
          <C size={9 * u} color={colors.custom_fireCream} numberOfLines={1}>{label}</C>
        </View>)}
      </View>
      {own ? <View style={[styles.quote, { borderLeftWidth: 2.5 * u, paddingLeft: 10 * u }]}>
        <C color={colors.onSurfaceInverse} numberOfLines={3} style={{ fontFamily: SERIF, fontStyle: "italic", fontSize: 13 * u, lineHeight: 18 * u }}>“{own}”</C>
      </View> : null}
      <View style={styles.between}>
        <C w="heavy" size={11.5 * u} color={colors.onSurfaceInverse}>jeelive.ai</C>
        <C w="bold" size={8.5 * u} color={colors.custom_fireCream} style={{ letterSpacing: 1.6 * u }}>SCORE 200+ WITH AI</C>
      </View>
    </View>
  </View>;
}

const styles = StyleSheet.create({
  card: { overflow: "hidden", backgroundColor: colors.custom_fireRed },
  face: { flex: 1, overflow: "hidden", justifyContent: "space-between", backgroundColor: colors.custom_fireRed },
  between: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  middle: { alignItems: "center" },
  hero: { flexDirection: "row", alignItems: "center", justifyContent: "center" },
  week: { flexDirection: "row", justifyContent: "center" },
  weekDay: { alignItems: "center" },
  dot: { alignItems: "center", justifyContent: "center" },
  dotDone: { backgroundColor: colors.onSurfaceInverse, borderColor: colors.onSurfaceInverse },
  dotToday: { backgroundColor: colors.custom_fireCream, borderColor: colors.onSurfaceInverse },
  dotOff: { backgroundColor: colors.custom_fireGlass, borderColor: colors.custom_fireLine },
  stats: { flexDirection: "row" },
  stat: { flex: 1, minWidth: 0, alignItems: "center", backgroundColor: colors.custom_fireGlass, borderWidth: 1, borderColor: colors.custom_fireLine },
  quote: { borderLeftColor: colors.custom_fireCream },
});
