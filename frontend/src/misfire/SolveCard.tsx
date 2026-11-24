// One Misfire question, solved again: the question as it was printed, the answer given in the paper, a fresh try, the
// right answer after a wrong try, the solution after any try, and "Samajh gaya" once the try is right.
import React, { useMemo, useState } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { imagePaths } from "@/src/assets/paperAssets";
import { piecesOf } from "@/src/assets/pieces";
import { AssetImage } from "@/src/components/AssetImage";
import { MathText } from "@/src/components/MathText";
import { PieceQuestion } from "@/src/components/Pieces";
import { Pill } from "@/src/components/design";
import { ErrorBox, Icon, Press, T, buzz } from "@/src/components/ui";
import { ToneTag } from "@/src/analysis/parts";
import { invalidate } from "@/src/useCached";
import { colors, space } from "@/src/theme";
import { MisfireItem, markDone, misfireKey, pictureRow, reopen, tryAgain } from "./api";
import { NumPad } from "./NumPad";
import { OUTCOME, chapterName, marks } from "./parts";
import { patchMisfire } from "./store";

export function SolveCard({ item, width, uid, onDone }: { item: MisfireItem; width: number; uid?: string; onDone?: () => void }) {
  const router = useRouter();
  const q = item.question || {};
  const row = useMemo(() => pictureRow(item), [item]);
  const [value, setValue] = useState("");
  // Solved right a moment ago and opened again: "Samajh gaya" is still one tap away.
  const [result, setResult] = useState<"right" | "wrong" | null>(item.status === "open" && item.tries > 0 && item.last_correct ? "right" : null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [solution, setSolution] = useState(false);
  const keys = Object.keys(q.options || {});
  const choice = item.type === "mcq" && keys.length > 0;
  const fixed = item.status === "fixed";
  const locked = busy || fixed || result === "right";
  const pieces = piecesOf(row);
  const typed: Record<string, string> = q.typed_options || {};
  const labelOf = (k?: string | null) => (k ? q.source_option_labels?.[k] || k : "");
  // A scanned question carries its options in the picture: the student taps the matching number.
  const tiles = q.render_mode === "source" && !Object.keys(typed).length;
  const [tag, tone, icon] = OUTCOME[item.outcome] || OUTCOME.incorrect;
  const chapter = chapterName(item.chapter);
  const questionPaths = pieces ? [] : imagePaths(item.attempt_id, row, "question");
  const solutionPaths = imagePaths(item.attempt_id, row, "solution");
  const pick = (k: string) => { setValue(v => (v === k ? "" : k)); setResult(null); };

  async function run(work: () => Promise<void>) {
    setBusy(true); setError("");
    try { await work(); } catch (e: any) { setError(e?.message || "Yeh abhi nahi ho paaya. Dobara try karo."); } finally { setBusy(false); }
  }
  const forget = () => { if (uid) invalidate(misfireKey(uid) + ".summary"); if (uid) invalidate(misfireKey(uid) + ".fixedids"); };
  const check = () => run(async () => {
    const res = await tryAgain(item.id, value.trim());
    patchMisfire(item.id, { tries: res.item?.tries ?? item.tries + 1, answer: res.item?.answer, solution_text: res.item?.solution_text, last_correct: res.correct, solution_count: res.item?.solution_count ?? item.solution_count });
    setResult(res.correct ? "right" : "wrong");
    buzz(res.correct ? "success" : "error");
  });
  const done = () => run(async () => { await markDone(item.id); patchMisfire(item.id, { status: "fixed" }); forget(); onDone?.(); });
  const undo = () => run(async () => { await reopen(item.id); patchMisfire(item.id, { status: "open", tries: 0, last_correct: false }); forget(); setResult(null); setValue(""); });

  return <View testID="misfire-solve-card" style={styles.card}>
    <View style={styles.tags}>
      <ToneTag label={tag} tone={tone} icon={icon} />
      {chapter ? <ToneTag label={chapter} tone="mute" /> : null}
      {item.lost ? <T testID="misfire-lost" size={12} w="bold" color={colors.error}>{marks(item.lost)} marks gaye</T> : null}
    </View>

    {pieces ? <PieceQuestion id={item.attempt_id} q={row} width={width} testPrefix="misfire" value={value} onPick={pick} disabled={locked} />
      : questionPaths.length ? questionPaths.map((path, i) => <AssetImage key={path} testID={`misfire-qimage-${i}`} path={path} label={`${item.subject} sawaal ${item.number}`} />)
        : q.text ? <MathText testID="misfire-question-text" text={q.text} />
          : <T testID="misfire-question-missing" size={13} color={colors.muted}>Is sawaal ki picture nahi mili. “Paper ka result” se ise poora dekh sakte ho.</T>}

    <T testID="misfire-paper-answer" size={12.5} color={colors.muted}>Paper mein aapka jawab: <T size={12.5} w="heavy" color={colors.custom_softText}>{labelOf(item.your_answer) || "chhoda tha"}</T></T>

    {fixed ? <View style={styles.fixed}>
      <View testID="misfire-fixed" style={styles.fixedTag}><Icon name="check-circle" size={18} color={colors.success} /><T w="heavy" size={14} color={colors.success}>Samajh gaya</T></View>
      <Pill testID="misfire-reopen" kind="outline" size="sm" icon="restart" label="Wapas list mein" busy={busy} onPress={undo} />
    </View> : <>
      {pieces && choice ? null : choice ? (tiles ? <View testID="misfire-tiles" accessibilityRole="radiogroup" style={styles.tiles}>
        {keys.map(k => {
          const on = value === k;
          return <Press key={k} testID={`misfire-option-${k}`} disabled={locked} onPress={() => pick(k)} scaleTo={0.96} accessibilityRole="radio" accessibilityState={{ checked: on }}
            accessibilityLabel={`Option ${labelOf(k)}${on ? ", chuna hua" : ""}`} style={[styles.tile, on && styles.on]}>
            <T w="mono" size={22} color={on ? colors.custom_pickInk : colors.onSurface}>{labelOf(k)}</T>
          </Press>;
        })}
      </View> : <View testID="misfire-options" accessibilityRole="radiogroup" style={{ gap: 10 }}>
        {keys.map(k => {
          const on = value === k, text = typed[k] || (String(q.options[k] ?? "").startsWith("See original") ? `Option ${labelOf(k)} (picture mein)` : String(q.options[k] ?? ""));
          return <Press key={k} testID={`misfire-option-${k}`} disabled={locked} onPress={() => pick(k)} scaleTo={0.985} accessibilityRole="radio" accessibilityState={{ checked: on }}
            accessibilityLabel={`Option ${labelOf(k)}${on ? ", chuna hua" : ""}`} style={[styles.option, on && styles.on]}>
            <View style={[styles.letter, on && styles.letterOn]}><T w="heavy" size={13} color={on ? colors.onSuccess : colors.custom_softText}>{labelOf(k)}</T></View>
            <View style={{ flex: 1 }}>{typed[k] ? <MathText testID={`misfire-option-math-${k}`} text={text} /> : <T size={15} w={on ? "heavy" : "medium"} color={on ? colors.onSurface : colors.custom_softText}>{text}</T>}</View>
          </Press>;
        })}
      </View>) : <NumPad value={value} onChange={v => { setValue(v); setResult(null); }} decimal={item.type !== "integer"} disabled={locked} />}

      {result === "right" ? <View testID="misfire-right" accessibilityRole="alert" style={[styles.verdict, { backgroundColor: colors.custom_successSoft }]}>
        <Icon name="check-circle" size={18} color={colors.success} /><T w="heavy" size={14} color={colors.success} style={{ flex: 1 }}>Sahi! Ab “Samajh gaya” dabao.</T>
      </View> : null}
      {result === "wrong" ? <View testID="misfire-wrong" accessibilityRole="alert" style={[styles.verdict, { backgroundColor: colors.custom_errorSoft }]}>
        <Icon name="close-circle" size={18} color={colors.error} /><T w="heavy" size={14} color={colors.error} style={{ flex: 1 }}>Galat. Sahi jawab: {labelOf(item.answer) || "—"}</T>
      </View> : null}
      {result === "right"
        ? <Pill testID="misfire-done" size="lg" icon="check" label="Samajh gaya" bg={colors.success} ink={colors.onSuccess} busy={busy} onPress={done} />
        : <Pill testID="misfire-check" size="lg" kind="brand" label="Check karo" busy={busy} disabled={!value.trim()} onPress={check} />}
    </>}

    <ErrorBox error={error} testID="misfire-error" />
    <View style={styles.links}>
      {item.tries > 0 ? <Press testID="misfire-show-solution" onPress={() => setSolution(s => !s)} accessibilityState={{ expanded: solution }} style={styles.link}>
        <Icon name="book-open-variant" size={16} color={colors.brandText} /><T w="heavy" size={13} color={colors.brandText}>{solution ? "Solution chhupao" : "Solution dekho"}</T>
      </Press> : <T testID="misfire-solution-hint" size={12} color={colors.muted} style={{ flex: 1 }}>Ek baar try karo, phir solution khulega.</T>}
      <Press testID="misfire-open-paper" onPress={() => router.push(`/result/${item.attempt_id}` as any)} style={styles.link}>
        <T w="heavy" size={13} color={colors.custom_softText}>Paper ka result</T><Icon name="arrow-right" size={15} color={colors.custom_softText} />
      </Press>
    </View>
    {solution && item.tries > 0 ? <View testID="misfire-solution" style={{ gap: space.sm }}>
      {item.answer ? <T size={12.5} color={colors.success} w="heavy">Sahi jawab: {labelOf(item.answer)}</T> : null}
      {solutionPaths.map((path, i) => <AssetImage key={path} testID={`misfire-simage-${i}`} path={path} label={`${item.subject} solution ${item.number}`} />)}
      {item.solution_text ? <MathText testID="misfire-solution-text" size={14} text={item.solution_text} /> : null}
      {!solutionPaths.length && !item.solution_text ? <T testID="misfire-no-solution" size={12.5} color={colors.muted}>Is sawaal ka likha hua solution nahi hai; upar sahi jawab diya hai.</T> : null}
    </View> : null}
  </View>;
}

const styles = StyleSheet.create({
  card: { gap: space.md, padding: space.lg, borderRadius: 22, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card },
  tags: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: 8 },
  tiles: { flexDirection: "row", gap: space.sm },
  tile: { flex: 1, minWidth: 0, height: 64, borderRadius: 18, borderWidth: 1.5, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, alignItems: "center", justifyContent: "center" },
  option: { flexDirection: "row", alignItems: "center", gap: 14, minHeight: 60, paddingHorizontal: space.lg, paddingVertical: space.md, borderRadius: 16, borderWidth: 1.5, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card },
  on: { borderColor: colors.custom_pickLine, backgroundColor: colors.custom_pickWash },
  letter: { width: 30, height: 30, borderRadius: 15, borderWidth: 1.5, borderColor: colors.custom_qFreshLine, alignItems: "center", justifyContent: "center" },
  letterOn: { backgroundColor: colors.custom_pick, borderColor: colors.custom_pick },
  verdict: { flexDirection: "row", alignItems: "center", gap: 8, padding: space.md, borderRadius: 14 },
  fixed: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: space.sm },
  fixedTag: { flexDirection: "row", alignItems: "center", gap: 6 },
  links: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: space.sm },
  link: { minHeight: 44, flexDirection: "row", alignItems: "center", gap: 6 },
});
