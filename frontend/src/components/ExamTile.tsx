import React from "react";
import { StyleSheet, View } from "react-native";
import { Icon, IconName, Press, T } from "@/src/components/ui";
import { colors, radius, space } from "@/src/theme";

export type TileKind = "jee" | "live" | "bitsat" | "comedk";
const SYMBOL: Record<TileKind, IconName> = { jee: "atom-variant", live: "trophy-outline", bitsat: "flask-outline", comedk: "school-outline" };

export function ExamTile({ kind, title, sub, badge, onPress, testID }: { kind: TileKind; title: string; sub: string; grad: [string, string]; badge?: string; onPress: () => void; testID: string }) {
  return <Press testID={testID} onPress={onPress} accessibilityLabel={`${title}. ${sub}`} scaleTo={0.97} style={styles.card}>
    <View style={styles.art}>
      <View pointerEvents="none" style={styles.orbit} />
      <View style={styles.symbol}><Icon name={SYMBOL[kind]} size={33} color={colors.brandText} /></View>
      {badge ? <View testID={`${testID}-badge`} style={styles.badge}><T w="heavy" size={9} color={colors.brandText}>{badge}</T></View> : null}
      <Icon name="arrow-top-right" size={17} color={colors.mutedSecondary} style={styles.arrow} />
    </View>
    <View style={styles.copy}>
      <T testID={`${testID}-title`} w="heavy" size={18} numberOfLines={1}>{title}</T>
      <T testID={`${testID}-description`} size={12} color={colors.muted} numberOfLines={1}>{sub}</T>
    </View>
  </Press>;
}

const styles = StyleSheet.create({
  card: { borderRadius: radius.lg, backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.brandLine, overflow: "hidden", minHeight: 163 },
  art: { height: 94, padding: space.lg, justifyContent: "flex-end", overflow: "hidden" },
  orbit: { position: "absolute", width: 132, height: 132, borderRadius: 66, borderWidth: 1, borderColor: colors.brandLine, top: -48, right: -48 },
  symbol: { width: 54, height: 54, borderRadius: 18, backgroundColor: colors.brandTertiary, alignItems: "center", justifyContent: "center" },
  badge: { position: "absolute", top: 12, right: 12, paddingHorizontal: 7, paddingVertical: 4, borderRadius: radius.pill, backgroundColor: colors.brandTertiary },
  arrow: { position: "absolute", right: 14, bottom: 12 },
  copy: { paddingHorizontal: space.lg, paddingBottom: space.lg, gap: 3 },
});