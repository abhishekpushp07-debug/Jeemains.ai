// Dream College Meter: the student's dream college + branch seats for one exam against their mock score.
// Look: a shining purple border and header (the College predictor's purple, with its light sweep) around a deep black
// body. Inside, each college is its own card with a diamond: royal blue, teal, royal blue, teal, royal blue. Each seat: marks it needs, a bar filling towards it, and "X marks door" in yellow
// (or "Pahunch mein ✓" in lime). The last mock and how far it moved from the one before sit on top.
// Used on Home (in place of the old promo), on the mock result and in the Rank tab's Dream panel (there with remove buttons).
import React from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Press, T } from "@/src/components/ui";
import { Pill } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { rankColors as colors, space } from "@/src/theme";
import { SERIF } from "@/src/rank/tones";
import { Shine } from "@/src/rank/controls";
import { Diamond } from "@/src/rank/Diamond";
import { Dream, DreamExam, dreamsOf, EXAM_NAME, FULL, MAX_DREAMS, Mock, mocksOf, removeDream, useDreams } from "./store";

const WHITE = colors.onBrandPrimary, SOFT = colors.custom_rankSilver, MUTED = colors.custom_rankSilverMuted;

export function DreamMeter({ exam, testID, mockId, editable, limit, onAdd, onMore }: {
  exam: DreamExam; testID: string; mockId?: string; editable?: boolean; limit?: number; onAdd?: () => void; onMore?: () => void;
}) {
  const s = useDreams();
  const dreams = dreamsOf(s, exam).slice().sort((a, b) => a.need - b.need);
  const mocks = mocksOf(s, exam);
  const at = mockId ? mocks.findIndex(m => m.id === mockId) : 0;
  const last: Mock | undefined = at >= 0 ? mocks[at] : undefined, prev: Mock | undefined = at >= 0 ? mocks[at + 1] : undefined;
  const shown = limit ? dreams.slice(0, limit) : dreams;
  return <View style={styles.glow}>
    <View testID={testID} style={styles.card}>
      <View style={styles.head}>
        <LinearGradient colors={[colors.custom_fPurpleFrom, colors.custom_fPurpleTo]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
        <Shine />
        <View style={styles.target}><Glyph name="bullseye-arrow" size={22} color={WHITE} /></View>
        <View style={{ flex: 1, gap: 2 }}>
          <T w="bold" size={10.5} color={colors.custom_fPurpleHint} style={styles.track} numberOfLines={1}>DREAM COLLEGE METER · {EXAM_NAME[exam].toUpperCase()}</T>
          <T color={WHITE} style={styles.title}>Kitne marks door?</T>
        </View>
        <T testID={`${testID}-count`} w="bold" size={12} color={colors.custom_fPurpleHint}>{dreams.length}/{MAX_DREAMS}</T>
      </View>

      <View style={styles.body}>
        {last ? <View testID={`${testID}-mock`} style={styles.mock}>
          <View style={{ flex: 1, gap: 2 }}>
            <T w="bold" size={10} color={MUTED} style={styles.track}>{mockId ? "IS MOCK MEIN" : "LAST MOCK"}</T>
            <View style={styles.scoreRow}>
              <T testID={`${testID}-score`} color={WHITE} style={styles.score}>{last.score}</T>
              <T w="semibold" size={14} color={MUTED}> / {FULL[exam]}</T>
            </View>
            <T size={11.5} color={MUTED} numberOfLines={1}>
              {last.title}{last.rawMax !== FULL[exam] ? ` · ${last.raw}/${last.rawMax} ko ${FULL[exam]} par scale kiya` : ""}
            </T>
          </View>
          {prev ? <Delta d={last.score - prev.score} testID={`${testID}-delta`} /> : null}
        </View> : <T testID={`${testID}-nomock`} size={12.5} color={SOFT}>
          Pehla full {EXAM_NAME[exam]} mock do. Har mock ke baad yahan dikhega har dream college kitne marks door hai.
        </T>}

        {dreams.length === 0 ? <View testID={`${testID}-empty`} style={styles.empty}>
          <T w="bold" size={15} color={WHITE}>Apne {MAX_DREAMS} dream college + branch chuno</T>
          <T size={12.5} color={SOFT}>College predictor mein kisi bhi college card par 🎯 Dream dabao. Har mock ke baad yahan dikhega kitne marks door ho.</T>
          {onAdd ? <Pill testID={`${testID}-add`} size="lg" label="Dream college chuno" iconRight="arrow-right" onPress={onAdd} bg={colors.custom_fBlood} ink={WHITE}
            style={styles.cta} /> : null}
        </View> : shown.map((d, i) => <DreamRow key={d.id} d={d} i={i} score={last?.score} testID={`${testID}-row-${i}`} editable={editable} />)}

        {limit && dreams.length > limit && onMore ? <Press testID={`${testID}-more`} onPress={onMore} style={styles.more} accessibilityRole="button">
          <T w="bold" size={13} color={WHITE}>Sab {dreams.length} dream dekho</T>
          <Glyph name="chevron-right" size={16} color={WHITE} />
        </Press> : null}
        {dreams.length > 0 && dreams.length < MAX_DREAMS && onAdd ? <Press testID={`${testID}-add-more`} onPress={onAdd} style={styles.more} accessibilityRole="button">
          <Glyph name="plus-circle-outline" size={16} color={WHITE} />
          <T w="bold" size={13} color={WHITE}>{MAX_DREAMS - dreams.length} aur dream jodo</T>
        </Press> : null}
        {dreams.length ? <T size={11} color={MUTED}>Marks normal paper ke hisaab se, 2026 cutoff par estimate. Guarantee nahi.</T> : null}
      </View>
    </View>
  </View>;
}

function Delta({ d, testID }: { d: number; testID: string }) {
  const ink = d > 0 ? colors.custom_fLime : d < 0 ? colors.custom_fPurpleDown : MUTED;
  return <View testID={testID} style={[styles.delta, { borderColor: ink }]}>
    <T w="heavy" size={13} color={ink}>{d > 0 ? `▲ ${d}` : d < 0 ? `▼ ${-d}` : "= 0"}</T>
    <T size={10} color={MUTED}>pichhle mock se</T>
  </View>;
}

// Row colours in order (max 5 dreams): royal blue, teal, royal blue, teal, royal blue, each with a diamond.
const ROYAL = { from: colors.custom_royalFrom, mid: colors.custom_royalMid, to: colors.custom_royalTo, ink: colors.custom_royalInk, gem: colors.custom_royalGlow };
const TEAL = { from: colors.custom_dreamTealFrom, mid: colors.custom_dreamTealMid, to: colors.custom_dreamTealTo, ink: colors.custom_tealInk, gem: colors.custom_tealInk };
const TONES = [ROYAL, TEAL];

function DreamRow({ d, i, score, testID, editable }: { d: Dream; i: number; score?: number; testID: string; editable?: boolean }) {
  const gap = score === undefined ? null : d.need - score;
  const done = gap !== null && gap <= 0;
  const fill = score === undefined ? 0 : Math.max(4, Math.min(100, (score / Math.max(1, d.need)) * 100));
  const tone = TONES[i % TONES.length];
  return <View testID={testID} style={[styles.row, done && styles.rowDone]}>
    <LinearGradient colors={[tone.from, tone.mid, tone.to]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    <View pointerEvents="none" style={styles.gem}><Diamond width={30} tint={tone.gem} sparkle opacity={0.9} /></View>
    <View style={styles.rowTop}>
      <View style={[styles.num, done && styles.numDone]}><T w="heavy" size={12} color={done ? colors.custom_fOn : WHITE}>{i + 1}</T></View>
      <View style={{ flex: 1, minWidth: 0, gap: 1 }}>
        <T w="bold" size={14} color={WHITE} numberOfLines={1}>{d.college}</T>
        <T size={12} color={tone.ink} numberOfLines={1}>{d.branch}</T>
      </View>
      {gap === null ? <View style={styles.right}>
        <T testID={`${testID}-need`} color={WHITE} style={styles.big}>{d.need}</T>
        <T w="bold" size={9.5} color={tone.ink} style={styles.track}>TARGET</T>
      </View> : done ? <View style={styles.right}>
        <T testID={`${testID}-reached`} w="heavy" size={14} color={colors.custom_fLime}>✓ Pahunch mein</T>
        <T size={11} color={colors.custom_fLime}>+{-gap} upar</T>
      </View> : <View style={styles.right}>
        <T testID={`${testID}-gap`} color={colors.custom_fYellow} style={styles.big}>{gap}</T>
        <T w="bold" size={9.5} color={colors.custom_fYellow} style={styles.track}>MARKS DOOR</T>
      </View>}
      {editable ? <Press testID={`${testID}-remove`} onPress={() => removeDream(d.id)} accessibilityLabel={`${d.college} dream se hatao`} style={styles.remove}>
        <Glyph name="close" size={16} color={tone.ink} />
      </Press> : null}
    </View>
    <View style={styles.track6}>
      <LinearGradient colors={done ? [colors.custom_fLime, colors.custom_fLime] : [colors.custom_fYellow, colors.custom_flame]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
        style={{ width: `${fill}%`, height: "100%", borderRadius: 3 }} />
    </View>
    <T size={11} color={tone.ink} numberOfLines={1} style={styles.noteGem}>
      Target {d.need}{d.range ? ` (${d.range[0]}–${d.range[1]})` : ""} / {FULL[d.exam]} · {d.note}
    </T>
  </View>;
}

const styles = StyleSheet.create({
  // Outer view carries the purple glow (a clipped view cannot cast a shadow); the card has a purple border and header only.
  glow: { borderRadius: 22, backgroundColor: colors.custom_dreamBody, shadowColor: colors.custom_fPurpleGlow, shadowOpacity: 0.75, shadowRadius: 20,
    shadowOffset: { width: 0, height: 4 }, elevation: 10 },
  card: { borderRadius: 22, overflow: "hidden", borderWidth: 1.5, borderColor: colors.custom_fPurpleGlow, backgroundColor: colors.custom_dreamBody },
  head: { flexDirection: "row", alignItems: "center", gap: space.md, padding: space.md, overflow: "hidden" },
  target: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_fPurpleChip,
    borderWidth: 1, borderColor: colors.custom_fPurpleGlassLine },
  track: { letterSpacing: 1.8 },
  title: { fontFamily: SERIF, fontSize: 22, lineHeight: 27 },
  body: { padding: space.md, gap: space.md, backgroundColor: colors.custom_dreamBody },
  mock: { flexDirection: "row", alignItems: "center", gap: space.md, padding: space.md, borderRadius: 16, borderWidth: 1,
    borderColor: colors.custom_dreamBodyLine, backgroundColor: colors.custom_dreamGlass },
  scoreRow: { flexDirection: "row", alignItems: "baseline" },
  score: { fontFamily: SERIF, fontSize: 32, lineHeight: 38 },
  delta: { alignItems: "center", paddingHorizontal: 10, paddingVertical: 6, borderRadius: 12, borderWidth: 1 },
  empty: { gap: space.sm },
  cta: { shadowColor: colors.custom_fBlood, shadowOpacity: 0.55, shadowRadius: 10, shadowOffset: { width: 0, height: 2 }, elevation: 5 },
  row: { gap: 6, padding: space.md, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_royalLine, overflow: "hidden" },
  rowDone: { borderColor: colors.custom_fLime },
  gem: { position: "absolute", right: 8, bottom: 6 },
  noteGem: { paddingRight: 34 },
  rowTop: { flexDirection: "row", alignItems: "center", gap: space.sm },
  num: { width: 26, height: 26, borderRadius: 13, alignItems: "center", justifyContent: "center", borderWidth: 1, borderColor: colors.custom_royalLine },
  numDone: { backgroundColor: colors.custom_fLime, borderColor: colors.custom_fLime },
  right: { alignItems: "flex-end" },
  big: { fontFamily: SERIF, fontSize: 24, lineHeight: 28 },
  remove: { width: 36, height: 36, alignItems: "center", justifyContent: "center" },
  track6: { height: 6, borderRadius: 3, overflow: "hidden", backgroundColor: colors.custom_dreamTrack },
  more: { flexDirection: "row", alignItems: "center", gap: 6, minHeight: 44 },
});
