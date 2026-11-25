// One question of Matched, as it was supplied (the JEE one, or one of ours): its words and its pictures; its options when
// asked for (`rows`); and, once its solution is open, the right answer and the worked solution.
// In the Matched paper the options can be tapped (`onPick`); looking back at the paper, the right one is green and a
// wrong choice is red.
// On a phone, maths is typeset: words and options that are only read are ONE page (./html.ts); options that are tapped
// are a row each. A question without maths, and every question on the web preview, is plain text and plain rows.
import React, { memo, useMemo, useState } from "react";
import { Platform, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import { plainMath, tex } from "@/src/components/AiSolution";
import { MathText } from "@/src/components/MathText";
import { OfflineMath } from "@/src/components/OfflineMath";
import { Glyph } from "@/src/components/Glyph";
import { Press, T } from "@/src/components/ui";
import { colors } from "@/src/theme";
import type { Picture, Side } from "./api";
import { LETTERS, optionsHtml, sideCss, stemHtml } from "./html";

const TYPESET = Platform.OS !== "web", MATH = /\$[^$]+\$|\\\(|\\\[/, PANEL = 12;
// The web preview has no typesetter: there the maths between $…$ is put into plain signs, and the words around it are left as they are.
const PIECE = /\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\$[^$]+?\$|\\\([\s\S]+?\\\)/g;
const plain = (s: string) => s.replace(PIECE, piece => plainMath(piece));
/** Words that may hold maths, on a coloured panel: typeset on a phone, plain on the web preview. */
const Words = ({ text, testID, size }: { text: string; testID: string; size: number }) => (TYPESET
  ? <MathText testID={testID} text={text} size={size} backgroundColor={colors.custom_pickWash} />
  : <T testID={testID} size={size} color={colors.custom_onReading} style={{ lineHeight: Math.round(size * 1.5) }}>{plain(text)}</T>);
const CSS = sideCss({ ink: colors.custom_onReading, soft: colors.custom_softText, line: colors.custom_cardLine, ring: colors.custom_qFreshLine,
  green: colors.custom_pick, greenInk: colors.custom_pickInk, greenLine: colors.custom_pickLine, wash: colors.custom_pickWash, onGreen: colors.onSuccess,
  red: colors.error, redWash: colors.custom_errorSoft });

/** A picture at the card's width; a tap makes it twice as wide (it then slides sideways), for small print. */
function PictureBox({ p, width, testID }: { p: Picture; width: number; testID: string }) {
  const [size, setSize] = useState(p.w && p.h ? { w: p.w, h: p.h } : null);
  const [big, setBig] = useState(false);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  if (failed) return <Press testID={`${testID}-retry`} onPress={() => { setFailed(false); setAttempt(a => a + 1); }} accessibilityLabel="Picture load nahi hui. Dobara try karo" style={styles.retry}>
    <T w="bold" size={12.5} color={colors.brandText}>Picture load nahi hui. Dobara try karo</T>
  </Press>;
  const w = Math.round(width * (big ? 2 : 1));
  // Until the picture says how big it is, its box is a wide strip; it never jumps for a picture that came with its size.
  const h = Math.round(w * (size ? size.h / size.w : 0.4));
  return <ScrollView horizontal scrollEnabled={big} showsHorizontalScrollIndicator={big} style={styles.paper}>
    <Pressable testID={testID} onPress={() => setBig(b => !b)} accessibilityRole="imagebutton" accessibilityLabel={big ? "Picture chhoti karo" : "Picture badi karo"}>
      <Image key={attempt} source={{ uri: p.url }} style={{ width: w, height: h }} contentFit="contain" transition={0} cachePolicy="disk"
        onLoad={e => { if (!size && e.source?.width && e.source?.height) setSize({ w: e.source.width, h: e.source.height }); }} onError={() => setFailed(true)} />
    </Pressable>
  </ScrollView>;
}

/** The options as rows: a round letter and the option. Green with a tick = right (once the solution is open); red with a
 *  cross = the student's wrong choice; yellow = chosen in a paper that is still being attempted. */
function Options({ options, right, wrong, picked, onPick, testID }: { options: string[]; right: number | null; wrong: number | null; picked: number | null; onPick?: (i: number) => void; testID: string }) {
  return <View testID={testID} accessibilityRole={onPick ? "radiogroup" : undefined} style={styles.options}>
    {options.map((o, i) => {
      const good = i === right, bad = i === wrong, on = !good && !bad && i === picked;
      const face = [styles.option, good && styles.optionRight, bad && styles.optionWrong, on && styles.optionOn];
      const inside = <>
        <View style={[styles.letter, good && styles.letterRight, bad && styles.letterWrong, on && styles.letterOn]}>
          <T w="heavy" size={12} color={good || bad ? colors.onSuccess : on ? colors.custom_matchedInk : colors.custom_softText}>{LETTERS[i]}</T>
        </View>
        {/* A typeset option must not take the tap from its row. */}
        {onPick && TYPESET && MATH.test(o) ? <View pointerEvents="none" style={styles.optionText}><MathText testID={`${testID}-${i}-text`} text={o} size={15} backgroundColor={on ? colors.custom_goldSoft : colors.custom_card} /></View>
          : <T size={15} color={colors.custom_onReading} style={styles.optionText}>{plain(o)}</T>}
        {good ? <View testID={`${testID}-right`}><Glyph name="check" size={16} color={colors.custom_pickInk} stroke={2.6} /></View> : null}
        {bad ? <View testID={`${testID}-wrong`}><Glyph name="close" size={16} color={colors.error} stroke={2.6} /></View> : null}
      </>;
      const label = `Option ${LETTERS[i]}${good ? ", sahi jawab" : bad ? ", aapka galat jawab" : on ? ", chuna hua" : ""}`;
      return onPick ? <Press key={i} testID={`${testID}-${i}`} onPress={() => onPick(i)} scaleTo={0.985} accessibilityRole="radio" accessibilityState={{ checked: on }} accessibilityLabel={label} style={face}>{inside}</Press>
        : <View key={i} testID={`${testID}-${i}`} accessibilityLabel={label} style={face}>{inside}</View>;
    })}
  </View>;
}

/** The opened solution: the right answer (with its letter when the options are shown), then the worked solution and its pictures. */
function Solution({ side, width, testID, rows }: { side: Side; width: number; testID: string; rows: boolean }) {
  const answer = side.correct != null ? (rows ? `(${LETTERS[side.correct]}) ` : "") + side.options[side.correct] : side.answer;
  const written = !!side.solution || side.solution_images.length > 0;
  return <View testID={`${testID}-solution`} style={styles.solution}>
    {answer ? <View style={styles.answer}>
      <Glyph name="check-circle-outline" size={20} color={colors.custom_pickInk} stroke={2} />
      <View style={styles.answerText}>
        <T w="heavy" size={10.5} color={colors.custom_pickInk} style={styles.caps}>SAHI JAWAB</T>
        <Words testID={`${testID}-answer`} text={answer} size={15} />
      </View>
    </View> : null}
    {side.solution ? <View style={styles.written}>
      <T w="heavy" size={10.5} color={colors.custom_eyebrow} style={styles.caps}>SOLUTION</T>
      <Words testID={`${testID}-solution-text`} text={side.solution} size={14} />
    </View> : null}
    {side.solution_images.map((p, i) => <PictureBox key={p.url + i} p={p} width={width - 2 * PANEL} testID={`${testID}-solution-image-${i}`} />)}
    {written ? null : <T testID={`${testID}-solution-none`} size={12.5} color={colors.muted}>{answer ? "Iska likha hua solution abhi nahi hai; sahi jawab upar diya hai." : "Is question ka solution abhi nahi aaya."}</T>}
  </View>;
}

/**
 * `rows` = its options are shown; `open` = its solution is open; `picked` = the option chosen in the paper (its place from
 * 0) and `onPick` = it can still be changed; `action` goes between the options and the solution; `paper` = the colour it
 * lies on (the typesetter's page takes it).
 */
export const QuestionBlock = memo(function QuestionBlock({ side, width, testID, open = false, rows = false, picked = null, onPick, action, paper = colors.custom_card }: {
  side: Side; width: number; testID: string; open?: boolean; rows?: boolean; picked?: number | null; onPick?: (i: number) => void; action?: React.ReactNode; paper?: string;
}) {
  const right = open ? side.correct : null, wrong = open && picked != null && picked !== side.correct ? picked : null;
  const list = rows && side.options.length > 0;
  const stem = TYPESET && MATH.test(side.text), typeset = TYPESET && list && !onPick && side.options.some(o => MATH.test(o));
  // Nothing stands between the words and the options, and the options are only read: one typesetter draws both.
  const one = list && !onPick && !side.images.length && (stem || typeset);
  const page = useMemo(() => (one ? stemHtml(side.text, tex) + optionsHtml(side.options, right, wrong, tex) : stem ? stemHtml(side.text, tex) : ""), [one, stem, side, right, wrong]);
  const typed = useMemo(() => (typeset && !one ? optionsHtml(side.options, right, wrong, tex) : ""), [typeset, one, side, right, wrong]);
  return <View style={styles.block}>
    {page ? <OfflineMath testID={`${testID}-text`} body={page} css={CSS} backgroundColor={paper} />
      : side.text ? <T testID={`${testID}-text`} size={15} color={colors.custom_onReading} style={styles.words}>{plain(side.text)}</T> : null}
    {side.images.map((p, i) => <PictureBox key={p.url + i} p={p} width={width} testID={`${testID}-image-${i}`} />)}
    {!list || one ? null : typed ? <OfflineMath testID={`${testID}-options`} body={typed} css={CSS} backgroundColor={paper} initialHeight={200} />
      : <Options options={side.options} right={right} wrong={wrong} picked={picked} onPick={onPick} testID={`${testID}-options`} />}
    {action}
    {open ? <Solution side={side} width={width} testID={testID} rows={rows} /> : null}
  </View>;
});

const styles = StyleSheet.create({
  block: { gap: 12 },
  words: { lineHeight: 23 },
  options: { gap: 8 },
  option: { flexDirection: "row", alignItems: "center", gap: 12, minHeight: 45, paddingVertical: 8, paddingHorizontal: 12, borderRadius: 14, borderWidth: 1.5, borderColor: colors.custom_cardLine },
  optionRight: { borderColor: colors.custom_pickLine, backgroundColor: colors.custom_pickWash },
  optionText: { flex: 1, minWidth: 0, lineHeight: 23 },
  letter: { width: 26, height: 26, borderRadius: 13, borderWidth: 1.5, borderColor: colors.custom_qFreshLine, alignItems: "center", justifyContent: "center" },
  letterRight: { backgroundColor: colors.custom_pick, borderColor: colors.custom_pick },
  optionWrong: { borderColor: colors.error, backgroundColor: colors.custom_errorSoft },
  letterWrong: { backgroundColor: colors.error, borderColor: colors.error },
  // Chosen in the paper: Matched's own yellow, so green keeps meaning "right".
  optionOn: { borderColor: colors.custom_glossYellow, backgroundColor: colors.custom_goldSoft },
  letterOn: { backgroundColor: colors.custom_glossYellow, borderColor: colors.custom_glossYellow },
  solution: { gap: 10, padding: PANEL, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_pickLine, backgroundColor: colors.custom_pickWash },
  answer: { flexDirection: "row", alignItems: "center", gap: 10 },
  answerText: { flex: 1, minWidth: 0 },
  written: { gap: 4 },
  caps: { letterSpacing: 1.4 },
  // Question pictures are printed on white: their paper stays white.
  paper: { flexGrow: 0, borderRadius: 10, backgroundColor: colors.custom_webWhite },
  retry: { minHeight: 44, justifyContent: "center" },
});
