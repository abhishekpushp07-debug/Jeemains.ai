import React from "react";
import { StyleSheet, View } from "react-native";
import { Icon, IconName, Press, T } from "@/src/components/ui";
import { colors, ExamCardKind, examCardColors, radius, space } from "@/src/theme";
import { ExamCardFinish } from "./ExamCardFinish";

export type TileKind = ExamCardKind;
const SYMBOL: Record<TileKind, IconName> = { jee: "atom-variant", live: "trophy-outline", bitsat: "flask-outline", comedk: "school-outline" };

export function ExamTile({ kind, title, sub, badge, shine = true, onPress, testID }: { kind: TileKind; title: string; sub: string; badge?: string; shine?: boolean; onPress: () => void; testID: string }) {
  const palette = examCardColors(kind);
  return <Press testID={testID} onPress={onPress} accessibilityLabel={`${title}. ${sub}`} scaleTo={0.97} style={[styles.card, { backgroundColor: palette.background, borderColor: palette.line }]}>
    {kind === "jee" || kind === "bitsat" ? <ExamCardFinish enabled={shine} kind={kind} testID={`${testID}-finish`} /> : null}
    <View style={styles.art}>
      <View pointerEvents="none" style={[styles.orbit, { borderColor: palette.line }]} />
      <View style={[styles.symbol, { backgroundColor: palette.iconBackground, borderColor: palette.line }]}><Icon name={SYMBOL[kind]} size={33} color={palette.accent} /></View>
      {badge ? <View testID={`${testID}-badge`} style={[styles.badge, { backgroundColor: palette.iconBackground, borderColor: palette.line }]}><T w="heavy" size={9} color={palette.accent}>{badge}</T></View> : null}
    </View>
    <View style={styles.copy}>
      <T testID={`${testID}-title`} w="heavy" size={18} color={palette.ink} style={styles.title}>{title}</T>
      <T testID={`${testID}-description`} size={12} color={palette.muted} style={styles.description}>{sub}</T>
      <View testID={`${testID}-open-label`} pointerEvents="none" style={[styles.open, { backgroundColor: palette.button }]}>
        <T size={12} w="heavy" color={palette.buttonInk}>Open</T>
        <Icon name="arrow-top-right" size={16} color={palette.buttonInk} />
      </View>
    </View>
  </Press>;
}

const styles = StyleSheet.create({
  card: { flex: 1, borderRadius: 18, borderWidth: 1, overflow: "hidden", minHeight: 250, shadowColor: colors.custom_webExamShadow, shadowOpacity: 0.14, shadowOffset: { width: 0, height: 14 }, shadowRadius: 28, elevation: 3 },
  art: { height: 94, padding: space.lg, justifyContent: "flex-end", overflow: "hidden" },
  orbit: { position: "absolute", width: 132, height: 132, borderRadius: 66, borderWidth: 1, top: -48, right: -48 },
  symbol: { width: 54, height: 54, borderRadius: 16, borderWidth: 1, alignItems: "center", justifyContent: "center" },
  badge: { position: "absolute", top: 12, right: 12, paddingHorizontal: 7, paddingVertical: 4, borderRadius: radius.pill, borderWidth: 1 },
  copy: { flex: 1, paddingHorizontal: space.lg, paddingBottom: space.lg, gap: 3 },
  title: { minHeight: 48 },
  description: { flex: 1, minHeight: 34 },
  open: { minHeight: 48, paddingHorizontal: space.md, marginTop: space.md, borderRadius: 10, flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
});