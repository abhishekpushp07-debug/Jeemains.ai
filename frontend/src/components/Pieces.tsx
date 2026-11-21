import React, { memo, useEffect, useMemo, useState } from "react";
import { Platform, ScrollView, StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import { assetDataUri, privateAssets } from "@/src/api/client";
import { imagePaths } from "@/src/assets/paperAssets";
import { FRAME, PIECE_ZOOM, pieceLayout, piecesOf } from "@/src/assets/pieces";
import { setPieceZoom, usePieceZoom } from "@/src/assets/pieceZoom";
import { colors, space } from "@/src/theme";
import { useImageValue } from "./AssetImage";
import { MathText } from "./MathText";
import { Icon, Press, T } from "./ui";

/** One cut picture at its exact size. Its box is kept before the picture arrives, so nothing on the screen jumps. */
const PieceImage = memo(function PieceImage({ path, width, height, label, testID }: { path: string; width: number; height: number; label: string; testID: string }) {
  const value = useImageValue(path);
  const source = useMemo(() => ({ uri: value?.uri, cacheKey: value?.cacheKey }), [value?.uri, value?.cacheKey]);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    if (value || failed) return;
    let alive = true;
    assetDataUri(path).catch(e => { if (alive && e?.name !== "AbortError") setFailed(true); });
    return () => { alive = false; };
  }, [path, value, failed]);
  // Inside an option card this sits in another button: fine on a phone, not allowed in a web page.
  if (failed) return (
    <Press testID={`${testID}-retry`} onPress={() => { privateAssets.invalidate(path); setFailed(false); }} accessibilityRole={Platform.OS === "web" ? "none" : "button"}
      accessibilityLabel={`${label}. Picture load nahi hui. Dobara try karo`} style={styles.retry}>
      <Icon name="refresh" size={15} color={colors.brandText} />
      <T w="bold" size={12} color={colors.brandText}>Dobara load karo</T>
    </Press>
  );
  if (!value) return <View testID={`${testID}-loading`} accessibilityLabel="Loading picture" style={[styles.wait, { width, height }]} />;
  return <Image testID={testID} source={source} recyclingKey={value.cacheKey || path} cachePolicy="memory" priority="high" transition={0} contentFit="contain"
    accessibilityLabel={label} style={{ width, height }} onError={() => setFailed(true)} />;
});

type Review = { correct: string[]; response?: string };

/** Smaller / larger text for cut questions (the website's two buttons). The test player has its own text-size button. */
function ZoomButtons({ step, testPrefix }: { step: number; testPrefix: string }) {
  const button = (by: -1 | 1) => {
    const off = by < 0 ? step === 0 : step === PIECE_ZOOM.length - 1;
    return (
      <Press testID={`${testPrefix}-zoom-${by < 0 ? "out" : "in"}`} disabled={off} onPress={() => setPieceZoom(step + by)}
        accessibilityLabel={by < 0 ? "Likhai chhoti karo" : "Likhai badi karo"} style={[styles.zoom, off && styles.zoomOff]}>
        <Icon name={by < 0 ? "magnify-minus-outline" : "magnify-plus-outline"} size={19} color={colors.custom_softText} />
      </Press>
    );
  };
  return (
    <View testID={`${testPrefix}-zoom`} style={styles.zoomRow}>
      <T testID={`${testPrefix}-zoom-size`} w="bold" size={11.5} color={colors.custom_eyebrow} style={styles.zoomLabel}>Likhai ka size · {Math.round(PIECE_ZOOM[step] * 100)}%</T>
      {button(-1)}{button(1)}
    </View>
  );
}

/** A question the website supplies in cut pieces: the question on its paper, then every option as a card that
 *  carries its own content. Answer mode picks an option in place; review mode marks the key and the student's pick. */
export function PieceQuestion({ id, q, width, version = "original", testPrefix = "player", value, onPick, disabled, review }: {
  id: string; q: any; width: number; version?: string; testPrefix?: string;
  value?: string; onPick?: (key: string) => void; disabled?: boolean; review?: Review;
}) {
  const pieces = useMemo(() => piecesOf(q) || [], [q]);
  const step = usePieceZoom(), zoom = PIECE_ZOOM[step];
  const [measured, setMeasured] = useState(0);
  const column = measured || width;
  const scale = useMemo(() => pieceLayout(pieces, q.typed_options, column, zoom), [pieces, q.typed_options, column, zoom]);
  const paths = useMemo(() => imagePaths(id, q, "piece", version), [id, q, version]);
  const labels: Record<string, string> = q.source_option_labels || {}, typed: Record<string, string> = q.typed_options || {};
  const firstStem = pieces.findIndex(p => p.part === "q");
  const draw = (i: number, label: string) => {
    const k = pieces[i].part === "q" ? scale.stem : scale.option;
    return <PieceImage key={paths[i]} path={paths[i]} width={pieces[i].w * k} height={pieces[i].h * k} label={label} testID={`${testPrefix}-piece-${i}`} />;
  };
  return (
    <View style={styles.root} onLayout={e => setMeasured(Math.round(e.nativeEvent.layout.width))}>
      {review ? <ZoomButtons step={step} testPrefix={testPrefix} /> : null}
      <View testID={`${testPrefix}-piece-stem`} style={styles.stem}>
        <ScrollView horizontal showsHorizontalScrollIndicator={zoom > 1} contentContainerStyle={styles.stemFit}>
          {pieces.map((p, i) => (p.part === "q" ? draw(i, (i === firstStem && q.accessible_text) || `Question ${q.number}`) : null))}
        </ScrollView>
      </View>
      {q.type === "integer" ? null : <>
        {review ? null : <T w="heavy" size={10} color={colors.custom_eyebrow} style={styles.eyebrow}>SELECT ONE ANSWER</T>}
        <View testID={`${testPrefix}-piece-options`} style={[styles.options, review && styles.optionsReview]}>
          {Object.keys(q.options || {}).map(key => {
            const i = pieces.findIndex(p => p.part === key), label = labels[key] || key;
            const paper = (
              <View testID={`${testPrefix}-option-paper-${key}`} style={[styles.paper, scale.stack ? styles.paperStack : styles.paperBeside]}>
                {typed[key] ? <View pointerEvents="none" style={styles.typed}><MathText testID={`${testPrefix}-option-math-${key}`} size={Math.round(15 * zoom)} text={typed[key]} backgroundColor={WHITE} /></View>
                  : i >= 0 ? <ScrollView horizontal showsHorizontalScrollIndicator={zoom > 1} style={styles.typed}>{draw(i, `Option ${label}`)}</ScrollView>
                    : <T testID={`${testPrefix}-option-math-${key}`} size={Math.round(15 * zoom)} color={colors.custom_softText}>Option {label}</T>}
              </View>
            );
            if (review) {
              const right = review.correct.includes(key), mine = !!review.response && review.response === key;
              const tone = right ? colors.success : colors.error, ink = right ? colors.onSuccess : colors.onError;
              return (
                <View key={key} testID={`${testPrefix}-option-card-${key}`} style={[styles.card, scale.stack && styles.cardStack, right ? styles.cardRight : mine ? styles.cardWrong : null]}
                  accessible accessibilityLabel={`Option ${label}${right && mine ? ", aapka jawab, sahi" : right ? ", sahi jawab" : mine ? ", aapka jawab" : ""}`}>
                  <View style={[styles.chip, scale.stack && styles.chipStack, (right || mine) && { backgroundColor: tone, borderColor: tone }]}>
                    <T w="mono" size={14} color={right || mine ? ink : colors.onSurface}>{label}</T>
                  </View>
                  {paper}
                  {right || mine ? (
                    <View testID={`${testPrefix}-option-mark-${key}`} style={[styles.mark, { backgroundColor: tone }]}>
                      <Icon name={right ? "check" : "close"} size={12} color={ink} />
                      <T w="heavy" size={10.5} color={ink}>{right && mine ? "Aapka jawab · Sahi" : right ? "Sahi jawab" : "Aapka jawab"}</T>
                    </View>
                  ) : null}
                </View>
              );
            }
            const on = value === key;
            const chip = (
              <View style={[styles.chip, on && styles.fill]}>
                <T testID={`${testPrefix}-option-label-${key}`} w="mono" size={14} color={on ? colors.onBrandPrimary : colors.onSurface}>{label}</T>
              </View>
            );
            const tick = <View style={[styles.tick, on && styles.fill]}>{on ? <Icon name="check" size={15} color={colors.onBrandPrimary} /> : null}</View>;
            return (
              <Press key={key} testID={`${testPrefix}-option-${key}`} disabled={disabled} onPress={() => onPick?.(key)} scaleTo={0.985}
                accessibilityLabel={`Option ${label}${on ? ", selected" : ""}`} accessibilityState={{ selected: on }} style={[styles.card, scale.stack && styles.cardStack, on && styles.cardOn]}>
                {scale.stack ? <><View style={styles.head}>{chip}{tick}</View>{paper}</> : <>{chip}{paper}{tick}</>}
              </Press>
            );
          })}
        </View>
      </>}
    </View>
  );
}

// The pictures are printed on white: their paper stays white in every theme.
const WHITE = colors.custom_webWhite;
const styles = StyleSheet.create({
  root: { alignSelf: "stretch", gap: space.md },
  stem: { backgroundColor: WHITE, borderRadius: 20, borderWidth: FRAME.stemLine, borderColor: colors.custom_cardLine, paddingHorizontal: FRAME.stemPad, paddingVertical: space.lg },
  stemFit: { flexDirection: "column", alignItems: "flex-start", gap: space.sm },
  eyebrow: { letterSpacing: 1.8 },
  options: { gap: 10 },
  optionsReview: { gap: 18, marginTop: 6 },
  card: { flexDirection: "row", alignItems: "center", gap: FRAME.gap, minHeight: 64, padding: FRAME.cardPad, borderRadius: 16, borderWidth: FRAME.cardLine, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card },
  cardOn: { borderColor: colors.brandPrimary, backgroundColor: colors.surfaceTertiary, shadowColor: colors.brandPrimary, shadowOpacity: 0.22, shadowRadius: 12, shadowOffset: { width: 0, height: 6 }, elevation: 3 },
  cardRight: { borderColor: colors.success, backgroundColor: colors.custom_successSoft },
  cardWrong: { borderColor: colors.error, backgroundColor: colors.custom_errorSoft },
  // Long options: the letter and the tick sit above the paper, which takes the whole card width.
  cardStack: { flexDirection: "column", alignItems: "stretch", gap: 8 },
  head: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  chipStack: { alignSelf: "flex-start" },
  chip: { width: FRAME.chip, height: FRAME.chip, borderRadius: FRAME.chip / 2, borderWidth: 1.5, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, alignItems: "center", justifyContent: "center" },
  tick: { width: FRAME.tick, height: FRAME.tick, borderRadius: FRAME.tick / 2, borderWidth: 1.5, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center" },
  fill: { backgroundColor: colors.brandPrimary, borderColor: colors.brandPrimary },
  paper: { minHeight: 42, justifyContent: "center", alignItems: "flex-start", overflow: "hidden", paddingHorizontal: FRAME.paperPad, paddingVertical: space.sm, borderRadius: 10, borderWidth: FRAME.paperLine, borderColor: colors.custom_cardLine, backgroundColor: WHITE },
  paperBeside: { flex: 1, minWidth: 0 },
  paperStack: { alignSelf: "stretch" },
  typed: { alignSelf: "stretch" },
  mark: { position: "absolute", top: -11, right: 14, height: 20, flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 9, borderRadius: 10 },
  wait: { borderRadius: 4, backgroundColor: colors.custom_cardRaised },
  retry: { minHeight: 44, flexDirection: "row", alignItems: "center", gap: 6 },
  zoomRow: { flexDirection: "row", alignItems: "center", gap: space.sm },
  zoomLabel: { flex: 1, letterSpacing: 0.3 },
  zoom: { width: 44, height: 44, borderRadius: 22, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, alignItems: "center", justifyContent: "center" },
  zoomOff: { opacity: 0.35 },
});
