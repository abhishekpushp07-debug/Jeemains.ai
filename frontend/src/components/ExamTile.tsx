import React, { useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import Constants from "expo-constants";
import { useReducedMotion } from "react-native-reanimated";
import { Icon, Press, T } from "@/src/components/ui";
import { colors, ExamCardKind, radius, space } from "@/src/theme";

export type TileKind = ExamCardKind;
const backend = Constants.expoConfig?.extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL;

// Owner's original artwork. Managed public storage is primary; identical bundled
// originals keep a phone's Home usable offline. Never recolour or replace icons.
const ORIGINAL: Record<TileKind, number> = {
  jee: require("../../assets/images/tile-jee.jpg"),
  live: require("../../assets/images/tile-live.jpg"),
  bitsat: require("../../assets/images/tile-bitsat.jpg"),
  comedk: require("../../assets/images/tile-comedk.jpg"),
};

export function ExamTile({ kind, title, sub, badge, onPress, testID }: {
  kind: TileKind; title: string; sub: string; badge?: string; shine?: boolean; onPress: () => void; testID: string;
}) {
  const reduced = useReducedMotion();
  const [fallback, setFallback] = useState(false);
  const [loaded, setLoaded] = useState(false);
  return <Press testID={testID} onPress={onPress} accessibilityLabel={`${title}. ${sub}`} scaleTo={reduced ? 1 : .97} style={styles.card}>
    <View testID={`${testID}-original-artwork`} style={styles.art}>
      <Image testID={`${testID}-image`} source={fallback ? ORIGINAL[kind] : { uri: `${backend}/api/brand/cards/${kind}.jpg` }}
        style={StyleSheet.absoluteFill} contentFit="cover" contentPosition="center" cachePolicy="memory-disk" transition={0}
        accessibilityLabel={`${title} original artwork`} onLoad={() => setLoaded(true)} onError={() => setFallback(true)} />
      {!loaded ? <ActivityIndicator testID={`${testID}-image-loading`} style={StyleSheet.absoluteFill} color={colors.custom_webWhite} /> : null}
      {badge ? <View testID={`${testID}-badge`} style={styles.badge}>
        <T testID={`${testID}-badge-label`} size={10} w="heavy" color={colors.custom_webWhite}>{badge}</T>
        <Icon name="star-four-points" size={9} color={colors.custom_webWhite} />
      </View> : null}
    </View>
    <View style={styles.copy}>
      <T testID={`${testID}-title`} w="heavy" size={16} style={styles.title}>{title}</T>
      <T testID={`${testID}-description`} size={12} color={colors.muted}>{sub}</T>
    </View>
  </Press>;
}

const styles = StyleSheet.create({
  card: { flex: 1, minHeight: 218, borderRadius: 18, overflow: "hidden", borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surfaceSecondary, shadowColor: colors.custom_webExamShadow, shadowOpacity: 1, shadowOffset: { width: 0, height: 8 }, shadowRadius: 16, elevation: 4 },
  art: { height: 136, overflow: "hidden", backgroundColor: colors.surfaceSecondary },
  badge: { position: "absolute", right: 10, top: 10, minHeight: 24, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_whiteA70, backgroundColor: colors.custom_darkCard, paddingHorizontal: 8, flexDirection: "row", alignItems: "center", gap: 3 },
  copy: { paddingHorizontal: space.lg, paddingVertical: space.md, gap: 3 },
  title: { minHeight: 40 },
});