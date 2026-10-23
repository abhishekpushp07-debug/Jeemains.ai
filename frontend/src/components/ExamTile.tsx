import React from "react";
import { View } from "react-native";
import { Image } from "expo-image";
import { Card, Icon, Press, T } from "@/src/components/ui";
import { colors, radius, space } from "@/src/theme";

export type TileKind = "jee" | "live" | "bitsat" | "comedk";

// Supplied premium artwork (3D glass icons, orbs, dots, tech lines) — kept exactly as designed.
const ART: Record<TileKind, number> = {
  jee: require("../../assets/images/tile-jee.jpg"),
  live: require("../../assets/images/tile-live.jpg"),
  bitsat: require("../../assets/images/tile-bitsat.jpg"),
  comedk: require("../../assets/images/tile-comedk.jpg"),
};

export function ExamTile({ kind, title, sub, grad, badge, onPress, testID }: { kind: TileKind; title: string; sub: string; grad: [string, string]; badge?: string; onPress: () => void; testID: string }) {
  return (
    <Press testID={testID} onPress={onPress} accessibilityLabel={`${title}. ${sub}`} scaleTo={0.95}
      style={{ borderRadius: 24, backgroundColor: colors.surfaceSecondary, shadowColor: grad[1], shadowOpacity: 0.2, shadowRadius: 16, shadowOffset: { width: 0, height: 8 }, elevation: 6 }}>
      <Card style={{ padding: 0, overflow: "hidden", borderRadius: 24, borderWidth: 0 }}>
        <View style={{ height: 136, backgroundColor: grad[0] }}>
          <Image source={ART[kind]} style={{ width: "100%", height: "100%" }} contentFit="cover" contentPosition="center" transition={0} accessibilityLabel={title + " artwork"} />
          {badge ? (
            <View testID={testID + "-badge"} style={{ position: "absolute", top: 10, right: 10, flexDirection: "row", alignItems: "center", gap: 3, paddingHorizontal: 8, height: 22, borderRadius: radius.pill, backgroundColor: kind === "jee" ? colors.custom_burgundy : colors.custom_seriesBright, borderWidth: 1, borderColor: colors.custom_whiteA70 }}>
              <T w="heavy" size={10} color={colors.onBrandPrimary} style={{ letterSpacing: 0.4 }}>{badge}</T>
              <Icon name="star-four-points" size={9} color={colors.onBrandPrimary} />
            </View>
          ) : null}
        </View>
        <View style={{ paddingHorizontal: space.lg, paddingVertical: space.md, gap: 2 }}>
          <T w="heavy" size={16} numberOfLines={1}>{title}</T>
          <T size={12} color={colors.muted} numberOfLines={1}>{sub}</T>
        </View>
      </Card>
    </Press>
  );
}
