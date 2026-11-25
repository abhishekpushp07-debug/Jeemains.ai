// One question of the Matched paper: OUR question with its options to tap (or a number to type), and under it the JEE
// Main question it matched, without options. After the paper is submitted the same card shows what was right, what the
// student chose, and the solution.
import React, { memo } from "react";
import { StyleSheet, View } from "react-native";
import { T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { NumPad } from "@/src/misfire/NumPad";
import { colors } from "@/src/theme";
import { PaperQuestion as Q, RIGHT, Verdict, WRONG } from "./paper";
import { QuestionBlock } from "./QuestionBlock";
import { BOX, PAD, Ribbon, Seal, SideHead, cardStyles } from "./parts";

const VERDICT: Record<Verdict, [string, string, string, "check" | "close" | "minus"]> = {
  right: [`Sahi! +${RIGHT}`, colors.custom_pickInk, colors.custom_pickWash, "check"],
  wrong: [`Galat. ${WRONG}`, colors.error, colors.custom_errorSoft, "close"],
  left: ["Yeh chhoda tha. 0", colors.custom_softText, colors.custom_cardRaised, "minus"],
};

/** `id` = what its test ids begin with; `value` = the answer given ("" = none yet); `result` = the paper is submitted and
 *  this is how the question went. */
export const PaperQuestion = memo(function PaperQuestion({ q, k, id, year, value, onChange, result, width }: {
  q: Q; k: number; id: string; year: string; value: string; onChange: (value: string) => void; result?: Verdict; width: number;
}) {
  const choice = q.ours.options.length > 0, typed = !choice && value ? value : "";
  const [words, ink, wash, icon] = VERDICT[result || "left"];
  const told = result ? <View testID={`${id}-verdict`} accessibilityRole="alert" style={[styles.verdict, { backgroundColor: wash }]}>
    <Glyph name={icon} size={16} color={ink} stroke={2.6} />
    <T w="heavy" size={13.5} color={ink} style={{ flex: 1 }}>{words}{typed ? `  ·  Aapka jawab: ${typed}` : ""}</T>
  </View> : null;
  return <View testID={id} style={cardStyles.card}>
    <Ribbon it={q} id={id} word={`Q${k + 1}`} />
    <View style={cardStyles.body}>
      <SideHead label="HAMARA QUESTION" tint={colors.custom_goldDeep} detail={q.ours.source} testID={`${id}-source`} />
      <QuestionBlock side={q.ours} width={width} testID={`${id}-ours`} rows open={!!result} picked={choice && value ? Number(value) : null}
        onPick={choice && !result ? i => onChange(value === String(i) ? "" : String(i)) : undefined}
        action={result ? told : choice ? undefined : <NumPad value={value} onChange={onChange} decimal />} />
      <Seal tag={q.ours.tag} testID={`${id}-tag`} />
      <View testID={`${id}-matched`} style={[cardStyles.panel, cardStyles.jee]}>
        <SideHead label={`JEE MAIN ${year} MEIN AAYA`} tint={colors.brandText} detail={q.n ? `Q${q.n}` : undefined} testID={`${id}-jee-number`} />
        <QuestionBlock side={q.jee} width={width - 2 * BOX} testID={`${id}-jee`} paper={colors.custom_chipBloodSoft} />
      </View>
    </View>
  </View>;
});

export const paperWidth = (screen: number, edge: number) => Math.min(screen, 720) - 2 * edge - 2 * PAD - 2;

const styles = StyleSheet.create({
  verdict: { flexDirection: "row", alignItems: "center", gap: 8, minHeight: 44, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 14 },
});
