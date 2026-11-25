// "Matched: JEE Mains questions matched with ours", in its four places: Home's card (it takes the All India series card's
// place once the series is over), the bar on the sign-in screen, the card at the top of the Matched page, and the card at
// the top of a shift, which leads to the shift's real paper on jeelive.ai ("Attempt all matched").
import React from "react";
import { StyleSheet, View, useWindowDimensions } from "react-native";
import { useRouter } from "expo-router";
import { Press, T } from "@/src/components/ui";
import { Pill } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { GlossWord } from "@/src/components/GlossWord";
import { Shine } from "@/src/analysis/Shine";
import { useCached } from "@/src/useCached";
import { useListFocus } from "@/src/useListFocus";
import { istDate } from "@/src/navigation";
import { colors, space } from "@/src/theme";
import { MatchedIndex, getIndex } from "./api";
import { Cup, Fireworks, MatchedBackdrop, matchedShine } from "./looks";

// Words on the card are a deep brown; on its brown button and chip they are pale yellow.
const INK = colors.custom_matchedInk, LIGHT = colors.custom_glossYellowHi;
const LINE = "JEE Mains questions matched with ours";
const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

export function HomeMatchedCard() {
  const router = useRouter();
  const narrow = useWindowDimensions().width < 360;
  const res = useCached<MatchedIndex>("matched.index", getIndex);
  useListFocus(res.revalidate);
  const d = res.data, latest = d?.shifts[0];
  const open = () => router.push("/matched" as any);
  return <View testID="home-matched">
    <Shine radius={28} {...matchedShine} sparkles={3} backdrop={<MatchedBackdrop />} face={styles.card}>
      <Fireworks testID="home-matched-fireworks" />
      <Press testID="home-matched-open" onPress={open} scaleTo={0.985} style={{ gap: space.lg }}
        accessibilityLabel={`Matched. ${LINE}.${d?.total ? ` ${plural(d.total, "question")} in ${plural(d.shifts.length, "shift")}.` : ""} Open`}>
        <View style={styles.top}>
          <View style={styles.chip}>
            <View style={styles.dot} />
            <T w="bold" size={10.5} color={INK} style={styles.caps} numberOfLines={1}>JEE MAIN</T>
          </View>
          {d?.shifts.length ? <View style={styles.count}><T testID="home-matched-shifts" w="heavy" size={10.5} color={LIGHT} style={{ letterSpacing: 1.2 }}>{plural(d.shifts.length, "shift").toUpperCase()}</T></View> : null}
        </View>
        <View style={styles.title}>
          <View style={styles.words}>
            <GlossWord testID="home-matched-title" size={narrow ? 28 : 33} look="ink">MATCHED</GlossWord>
            <T testID="home-matched-line" w="semibold" size={narrow ? 13.5 : 14.5} color={INK}>{LINE}</T>
          </View>
          <Cup testID="home-matched-cup" size={narrow ? 124 : 146} lift={26} />
        </View>
        <View testID="home-matched-facts" style={styles.facts}>
          {d?.total && latest ? <>
            <View style={styles.fact}>
              <T testID="home-matched-total" w="heavy" size={narrow ? 20 : 23} color={INK} numberOfLines={1}>{d.total}</T>
              <T size={11} color={INK} numberOfLines={1}>questions matched</T>
            </View>
            <View style={[styles.fact, styles.factLine]}>
              <T testID="home-matched-latest" w="heavy" size={narrow ? 15 : 17} color={INK} numberOfLines={1}>{istDate(latest.day)} · Shift {latest.shift}</T>
              <T size={11} color={INK} numberOfLines={1}>latest shift</T>
            </View>
          </> : <T testID="home-matched-soon" w="medium" size={12.5} color={INK} style={styles.soon}>
            {d ? "JEE Main ke har shift ke baad yahan woh questions aayenge jo hamare questions se match hue." : res.error ? "Abhi load nahi hua. Kholo aur dobara try karo." : "Dekh rahe hain…"}
          </T>}
        </View>
      </Press>
      <Pill testID="home-matched-cta" label={d?.total ? "See matched questions" : "Open Matched"} iconRight="arrow-right" bg={INK} ink={LIGHT} style={styles.cta} onPress={open} />
    </Shine>
  </View>;
}

/** The sign-in screen's bar: people who have no account yet can open Matched too. */
export function MatchedBanner() {
  const router = useRouter();
  return <Press testID="entry-matched" onPress={() => router.push("/matched" as any)} scaleTo={0.985} style={styles.barPress} accessibilityLabel={`Matched. ${LINE}. Open`}>
    <Shine radius={20} {...matchedShine} ring={2} band={64} backdrop={<MatchedBackdrop />} face={styles.bar}>
      <View style={{ flex: 1, minWidth: 0 }}>
        <GlossWord testID="entry-matched-title" size={19} look="ink">MATCHED</GlossWord>
        <T testID="entry-matched-line" w="semibold" size={12.5} color={INK} numberOfLines={2}>{LINE}</T>
      </View>
      <View style={styles.go}>
        <T w="heavy" size={13} color={LIGHT}>Dekho</T>
        <Glyph name="arrow-right" size={15} color={LIGHT} stroke={2} />
      </View>
    </Shine>
  </Press>;
}

/** The Matched page's top card. */
export function MatchedHero({ total, shifts }: { total: number; shifts: number }) {
  return <Shine radius={24} {...matchedShine} sparkles={3} backdrop={<MatchedBackdrop />} face={styles.hero}>
    <Fireworks />
    <View style={styles.words}>
      <GlossWord testID="matched-hero-title" size={26} look="ink">MATCHED</GlossWord>
      <T w="semibold" size={13.5} color={INK}>{LINE}</T>
      {total ? <View style={styles.heroCount}>
        <GlossWord testID="matched-total" size={40} look="ink">{String(total)}</GlossWord>
        <T testID="matched-total-line" w="bold" size={14} color={INK} style={styles.countLine}>questions matched{"\n"}in {plural(shifts, "shift")}</T>
      </View> : null}
    </View>
    <Cup testID="matched-hero-cup" size={total ? 140 : 104} lift={total ? 16 : 18} />
  </Shine>;
}

/**
 * A shift's top card: how many of its questions matched ours, and the way into the shift's real paper on jeelive.ai
 * ("Attempt all matched"). `questions` = how many of ours are in that paper (0 = no paper is attached to the shift yet);
 * `note` = the line above the button.
 */
export function AttemptCard({ matched, asked, year, questions, note, onAttempt }: {
  matched: number; asked: number | null; year: string; questions: number; note: string; onAttempt: () => void;
}) {
  return <Shine radius={24} {...matchedShine} sparkles={3} backdrop={<MatchedBackdrop />} face={styles.attempt}>
    <Fireworks testID="matched-shift-fireworks" />
    <View style={styles.title}>
      <View style={styles.words}>
        <View style={[styles.chip, styles.chipLeft]}>
          <View style={styles.dot} />
          <T testID="matched-shift-line" w="bold" size={10.5} color={INK} style={styles.caps} numberOfLines={1}>JEE MAIN {year}</T>
        </View>
        <View style={styles.shiftCount}>
          <GlossWord testID="matched-shift-count" size={44} look="ink">{String(matched)}</GlossWord>
          <T testID="matched-shift-count-line" w="bold" size={14.5} color={INK} style={styles.countLine}>{asked ? `of ${asked} questions\nmatched with ours` : `question${matched === 1 ? "" : "s"}\nmatched with ours`}</T>
        </View>
        {asked ? <View style={styles.track} accessibilityRole="progressbar" accessibilityLabel={`${matched} of ${asked} matched`}>
          <View style={[styles.fill, { width: `${Math.max(4, Math.round(matched / asked * 100))}%` }]} />
        </View> : null}
      </View>
      <Cup testID="matched-shift-cup" size={156} lift={12} />
    </View>
    {questions ? <>
      <View testID="matched-attempt-facts" style={styles.facts}>
        <View style={styles.fact}><T testID="matched-attempt-questions" w="heavy" size={20} color={INK}>{questions}</T><T size={11} color={INK}>{questions === 1 ? "question" : "questions"}</T></View>
        <View style={[styles.fact, styles.factLine]}><T w="heavy" size={20} color={INK}>{questions * 4}</T><T size={11} color={INK}>marks</T></View>
        <View style={[styles.fact, styles.factLine]}><T w="heavy" size={20} color={INK}>+4 / −1</T><T size={11} color={INK}>marking</T></View>
      </View>
      <T testID="matched-attempt-note" w="semibold" size={12.5} color={INK} style={styles.note}>{note}</T>
      <Pill testID="matched-attempt" label="Attempt all matched" iconRight="arrow-right" bg={INK} ink={LIGHT} size="lg" style={styles.cta} onPress={onAttempt} />
    </> : matched ? <T testID="matched-attempt-soon" w="medium" size={12.5} color={INK}>Is shift ke matched sawaalon ka paper jald yahan khulega.</T> : null}
  </Shine>;
}

const styles = StyleSheet.create({
  title: { flexDirection: "row", alignItems: "center" },
  words: { flex: 1, minWidth: 0, gap: 2 },
  attempt: { padding: 16, gap: space.md },
  shiftCount: { flexDirection: "row", alignItems: "center", gap: 10 },
  countLine: { flexShrink: 1, lineHeight: 19 },
  chipLeft: { alignSelf: "flex-start", marginBottom: 4 },
  note: { textAlign: "center", lineHeight: 18 },
  track: { height: 8, borderRadius: 4, marginTop: 6, overflow: "hidden", backgroundColor: colors.custom_matchedTrack },
  fill: { height: 8, borderRadius: 4, backgroundColor: INK },
  // 17 inside the 3-point running edge: the same 20 from the card's outer edge as the All India card it replaces.
  card: { padding: 17, gap: space.lg },
  top: { flexDirection: "row", alignItems: "center", gap: space.sm },
  chip: { flexDirection: "row", alignItems: "center", gap: 7, height: 28, paddingHorizontal: 11, borderRadius: 999, borderWidth: 1, borderColor: colors.custom_matchedLine, backgroundColor: colors.custom_matchedGlass, flexShrink: 1 },
  dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: INK },
  caps: { letterSpacing: 2 },
  // On the white glow of the corner: a brown chip with pale yellow words, so it reads on any phone.
  count: { height: 26, paddingHorizontal: 10, borderRadius: 13, backgroundColor: INK, alignItems: "center", justifyContent: "center" },
  facts: { flexDirection: "row", alignItems: "center", minHeight: 66, borderRadius: 18, borderWidth: 1, borderColor: colors.custom_matchedLine, backgroundColor: colors.custom_matchedGlass, paddingVertical: 12 },
  fact: { flex: 1, minWidth: 0, alignItems: "center", gap: 1, paddingHorizontal: 4 },
  factLine: { borderLeftWidth: 1, borderLeftColor: colors.custom_matchedLine },
  soon: { flex: 1, textAlign: "center", paddingHorizontal: space.md },
  cta: { borderRadius: 16 },
  barPress: { borderRadius: 20 },
  bar: { flexDirection: "row", alignItems: "center", gap: space.md, paddingVertical: 12, paddingHorizontal: 14 },
  go: { flexDirection: "row", alignItems: "center", gap: 5, height: 44, paddingHorizontal: 14, borderRadius: 22, backgroundColor: INK },
  hero: { flexDirection: "row", alignItems: "center", padding: 16 },
  heroCount: { flexDirection: "row", alignItems: "center", gap: space.md, marginTop: space.sm },
});
