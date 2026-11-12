import React from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { Pill } from "@/src/components/design";
import { colors, space } from "@/src/theme";
import { usesNativeTabs } from "@/src/navigation";

// Placeholder tab: the rank feature is planned but not built yet, so nothing here pretends to rank anyone.
export default function RankTab() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  return (
    <ScrollView testID="rank-screen" style={{ flex: 1, backgroundColor: colors.surface }}
      contentContainerStyle={{ paddingTop: insets.top + space.lg, paddingBottom: (usesNativeTabs ? insets.bottom : 0) + space.xxl, paddingHorizontal: space.lg, gap: space.xl }}>
      <View style={{ gap: 2 }}>
        <T w="bold" size={11} color={colors.custom_eyebrow} style={styles.caps}>ALL INDIA RANK</T>
        <T testID="rank-title" w="heavy" size={30}>your rank.</T>
        <T testID="rank-subtitle" w="heavy" size={30} color={colors.custom_eyebrow}>coming soon.</T>
      </View>

      <View testID="rank-hero" style={styles.hero}>
        <LinearGradient colors={[colors.custom_seriesFrom, colors.custom_seriesMid, colors.custom_seriesTo]} locations={[0, 0.55, 1]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
        <View style={styles.podium}><Glyph name="podium" size={40} color={colors.onSurfaceInverse} stroke={1.3} /></View>
        <View testID="rank-soon-badge" style={styles.badge}>
          <View style={styles.dot} />
          <T w="bold" size={10.5} color={colors.onSurfaceInverse} style={styles.caps}>BEING BUILT</T>
        </View>
        <T w="heavy" size={21} color={colors.onSurfaceInverse} style={styles.center}>Your place among every aspirant.</T>
        <T size={13.5} color={colors.custom_whiteA70} style={styles.center}>We’re building rank right now. Until it’s ready, your scores and results stay safe in My Tests.</T>
      </View>

      <View style={{ gap: space.md }}>
        <Pill testID="rank-open-series" size="lg" label="Open All India series" iconRight="arrow-right" onPress={() => router.push("/live")} />
        <Pill testID="rank-open-results" kind="outline" label="See my results" icon="chart-box-outline"
          onPress={() => router.push({ pathname: "/(tabs)/tests", params: { tab: "completed", at: String(Date.now()) } })} />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  caps: { letterSpacing: 2.2 },
  hero: { borderRadius: 28, overflow: "hidden", padding: space.xl, paddingVertical: 36, alignItems: "center", gap: space.md, backgroundColor: colors.custom_series, borderWidth: 1, borderColor: colors.custom_webGlassLine },
  podium: { width: 84, height: 84, borderRadius: 42, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_webGlass, borderWidth: 1, borderColor: colors.custom_webGlassLine },
  badge: { flexDirection: "row", alignItems: "center", gap: 7, height: 28, paddingHorizontal: 12, borderRadius: 999, borderWidth: 1, borderColor: colors.custom_webGlassLine, backgroundColor: colors.custom_webGlass },
  dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: colors.brandPrimary },
  center: { textAlign: "center" },
});
