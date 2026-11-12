import React, { useState } from "react";
import { ActivityIndicator, StyleSheet, View, useWindowDimensions } from "react-native";
import { Image } from "expo-image";
import Constants from "expo-constants";
import { useReducedMotion } from "react-native-reanimated";
import { Press, T } from "@/src/components/ui";
import { colors, ExamCardKind, examGlow, space } from "@/src/theme";

export type TileKind = ExamCardKind;
const backend = Constants.expoConfig?.extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL;

// Owner's original artwork. Managed public storage is primary; identical bundled
// originals keep a phone's Home usable offline. Never recolour or replace icons.
export const ORIGINAL_ART: Record<TileKind, number> = {
  jee: require("../../assets/images/tile-jee.jpg"),
  live: require("../../assets/images/tile-live.jpg"),
  bitsat: require("../../assets/images/tile-bitsat.jpg"),
  comedk: require("../../assets/images/tile-comedk.jpg"),
};

/** Original 3D art, cropped to its centre icon in a rounded frame. */
export function ExamArt({ kind, size, testID, label }: { kind: TileKind; size: number; testID: string; label: string }) {
  const [fallback, setFallback] = useState(false);
  const [loaded, setLoaded] = useState(false);
  return <View testID={`${testID}-original-artwork`} style={[styles.art, { width: size, height: size, borderRadius: Math.round(size * 0.28) }]}>
    <Image testID={`${testID}-image`} source={fallback ? ORIGINAL_ART[kind] : { uri: `${backend}/api/brand/cards/${kind}.jpg` }}
      style={StyleSheet.absoluteFill} contentFit="cover" contentPosition="center" cachePolicy="memory-disk" transition={0}
      accessibilityLabel={`${label} original artwork`} onLoad={() => setLoaded(true)} onError={() => setFallback(true)} />
    {!loaded ? <ActivityIndicator testID={`${testID}-image-loading`} style={StyleSheet.absoluteFill} color={colors.custom_webWhite} /> : null}
  </View>;
}

export function ExamTile({ kind, title, sub, badge, onPress, testID }: {
  kind: TileKind; title: string; sub: string; badge?: string; onPress: () => void; testID: string;
}) {
  const reduced = useReducedMotion();
  const narrow = useWindowDimensions().width < 360;
  const glow = examGlow(kind);
  const live = kind === "live";
  return <Press testID={testID} onPress={onPress} accessibilityLabel={`${title}. ${sub}`} scaleTo={reduced ? 1 : .97} style={styles.press}>
    <View style={[styles.card, live ? styles.live : styles.plain]}>
      <View pointerEvents="none" style={styles.clip}><View style={[styles.wash, { backgroundColor: glow }, live && { opacity: 0.4 }]} /></View>
      <View pointerEvents="none" style={[styles.halo, { backgroundColor: glow }]} />
      <View style={styles.pop}><ExamArt kind={kind} size={62} testID={testID} label={title} /></View>
      {badge ? <View testID={`${testID}-badge`} style={[styles.badge, { backgroundColor: kind === "jee" || live ? colors.brandPrimary : colors.custom_cardRaised }]}>
        <T testID={`${testID}-badge-label`} size={10} w="heavy" color={colors.custom_webWhite} style={{ letterSpacing: 0.6 }}>{badge}</T>
      </View> : <View style={{ height: 22 }} />}
      <View style={{ flex: 1 }} />
      <T testID={`${testID}-title`} w="heavy" size={narrow ? 14.5 : 16} numberOfLines={2}>{title}</T>
      <T testID={`${testID}-description`} size={12} numberOfLines={2} color={live ? colors.custom_seriesBright : colors.muted}>{sub}</T>
    </View>
  </Press>;
}

const styles = StyleSheet.create({
  press: { flex: 1 },
  card: { flex: 1, minHeight: 136, borderRadius: 22, padding: space.lg, paddingTop: 14, gap: 2, borderWidth: 1 },
  plain: { backgroundColor: colors.custom_card, borderColor: colors.custom_cardLine },
  live: { backgroundColor: colors.custom_series, borderColor: colors.brandLine },
  clip: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0, borderRadius: 22, overflow: "hidden" },
  wash: { position: "absolute", width: 170, height: 170, borderRadius: 85, top: -96, right: -70, opacity: 0.22 },
  halo: { position: "absolute", width: 82, height: 82, borderRadius: 41, top: -22, right: 0, opacity: 0.28 },
  pop: { position: "absolute", top: -14, right: 10, transform: [{ rotate: "-6deg" }], shadowColor: colors.custom_bar, shadowOpacity: 0.6, shadowRadius: 10, shadowOffset: { width: 0, height: 8 }, elevation: 10 },
  art: { overflow: "hidden", backgroundColor: colors.custom_cardRaised, borderWidth: 1.5, borderColor: colors.custom_whiteA15 },
  badge: { alignSelf: "flex-start", height: 22, borderRadius: 11, paddingHorizontal: 9, justifyContent: "center" },
});
