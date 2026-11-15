import React from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInDown, useReducedMotion } from "react-native-reanimated";
import { IconName, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { DCard, IconCircle, Pill, SectionLabel } from "@/src/components/design";
import { useShare } from "@/src/components/SeriesBanner";
import { colors, space } from "@/src/theme";
import { usesNativeTabs } from "@/src/navigation";

const STEPS: { icon: IconName; title: string; body: string }[] = [
  { icon: "database-search-outline", title: "Every PYQ, studied", body: "Each previous-year JEE question is analysed by AI on 80 parameters — concept, sub-topic, difficulty, trap type, time cost, formula family and more." },
  { icon: "chart-timeline-variant-shimmer", title: "Patterns become papers", body: "Those patterns guide which concepts, mixes and difficulty curves each test series paper practises — the series’ AI-led prediction and estimation approach." },
  { icon: "lightning-bolt-outline", title: "Concepts become cards", body: "Rapid Fire turns the most-tested formulas and concepts into 15-second recall cards, so revision fits into any 3 minutes." },
  { icon: "heart-outline", title: "Free for every student", body: "No fees, no paywall. Practice, analysis and solutions are free for all — because every aspirant deserves a fair shot." },
];

export default function Mission() {
  const insets = useSafeAreaInsets();
  const share = useShare();
  const reduced = useReducedMotion();
  const enter = (i: number) => reduced ? undefined : FadeInDown.delay(70 * i).duration(340);
  return (
    <ScrollView testID="mission-screen" style={{ flex: 1, backgroundColor: colors.surface }} contentContainerStyle={{ paddingTop: insets.top + space.lg, paddingBottom: (usesNativeTabs ? insets.bottom : 0) + space.xxl, paddingHorizontal: space.lg, gap: space.xl }}>
      <Animated.View entering={enter(0)} style={{ gap: space.md }}>
        <View style={styles.brand}>
          <View style={styles.ai}><T w="bold" size={10} color={colors.brandText}>100% AI</T></View>
          <Glyph name="creation" size={14} color={colors.custom_eyebrow} />
          <T size={12} color={colors.custom_eyebrow}>Created by <T w="heavy" size={12} color={colors.custom_softText}>AI Astra</T></T>
        </View>
        <T w="heavy" size={10} color={colors.brandText} style={{ letterSpacing: 2.4 }}>OUR MISSION</T>
        <T w="heavy" size={30}>Built by AI.{"\n"}Made for you.</T>
        <T size={14} color={colors.muted}>JEELIVE.AI’s practice content and test series are designed by AI analysing every PYQ question on 80 parameters, aiming for the world’s best prediction and estimation of what to practise.</T>
        <View style={styles.stats}>
          {[["80", "parameters"], ["62", "daily mocks"], ["₹0", "forever"]].map(([a, b], i) => (
            <View key={b} style={[styles.stat, i > 0 && styles.statLine]}>
              <T w="heavy" size={24}>{a}</T>
              <T size={11.5} color={colors.custom_eyebrow}>{b}</T>
            </View>
          ))}
        </View>
      </Animated.View>

      <View style={{ gap: space.sm }}>
        <SectionLabel title="How it works" />
        <DCard style={{ padding: 0 }}>
          {STEPS.map((s, i) => (
            <Animated.View key={s.title} entering={enter(i + 1)} style={[styles.step, i > 0 && styles.stepLine]}>
              <IconCircle icon={s.icon} color={colors.custom_softText} size={42} />
              <View style={{ flex: 1, gap: 3 }}>
                <T w="heavy" size={15}>{s.title}</T>
                <T size={12.5} color={colors.muted}>{s.body}</T>
              </View>
            </Animated.View>
          ))}
        </DCard>
      </View>

      <DCard style={styles.share}>
        <Image source={require("../../assets/images/jeelive-icon.png")} style={styles.icon} />
        <T w="heavy" size={20} style={{ textAlign: "center" }}>It’s free. Pass it on.</T>
        <T size={13} color={colors.muted} style={{ textAlign: "center" }}>Share JEELIVE.AI with your friends, batchmates and juniors. One share can change someone’s preparation.</T>
        <Pill testID="mission-share-button" size="lg" label="Share with friends" icon="share-variant" onPress={share} style={{ alignSelf: "stretch" }} />
      </DCard>

      <T size={11} color={colors.custom_eyebrow} testID="mission-disclaimer">
        “80 parameters”, “100% AI” and “world best” describe the creator’s stated AI-led design approach and ambition — not an independent audit, verified ranking or guarantee. Supplied solutions remain the original source. Score goals are practice targets, not promised results. Not affiliated with NTA.
      </T>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  brand: { flexDirection: "row", alignItems: "center", gap: 6, flexWrap: "wrap" },
  ai: { backgroundColor: colors.brandTertiary, borderWidth: 1, borderColor: colors.brandLine, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4, marginRight: 4 },
  stats: { flexDirection: "row", marginTop: space.sm, paddingVertical: space.md, borderTopWidth: 1, borderBottomWidth: 1, borderColor: colors.custom_cardLine },
  stat: { flex: 1, gap: 2, paddingHorizontal: space.md },
  statLine: { borderLeftWidth: 1, borderLeftColor: colors.custom_cardLine },
  step: { flexDirection: "row", gap: space.md, padding: space.lg, alignItems: "flex-start" },
  stepLine: { borderTopWidth: 1, borderTopColor: colors.custom_barLine },
  share: { alignItems: "center", gap: space.md, padding: space.xl },
  icon: { width: 56, height: 56, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLineStrong },
});
