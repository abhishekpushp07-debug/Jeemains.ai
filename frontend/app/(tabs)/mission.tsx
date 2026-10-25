import React from "react";
import { ScrollView, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Image } from "expo-image";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInDown } from "react-native-reanimated";
import { Button, Card, Icon, IconName, T } from "@/src/components/ui";
import { useShare } from "@/src/components/SeriesBanner";
import { colors, radius, space } from "@/src/theme";
import { usesNativeTabs } from "@/src/navigation";

const STEPS: { icon: IconName; title: string; body: string }[] = [
  { icon: "database-search-outline", title: "Every PYQ, studied", body: "Each previous-year JEE question is analysed by AI on 80 parameters — concept, sub-topic, difficulty, trap type, time cost, formula family and more." },
  { icon: "chart-timeline-variant-shimmer", title: "Patterns become papers", body: "Those patterns guide which concepts, mixes and difficulty curves each test series paper practises — the series’ AI-led prediction and estimation approach." },
  { icon: "lightning-bolt-circle", title: "Concepts become cards", body: "Rapid Fire turns the most-tested formulas and concepts into 20-second recall cards, so revision fits into any 3 minutes." },
  { icon: "account-heart-outline", title: "Free for every student", body: "No fees, no paywall. Practice, analysis and solutions are free for all — because every aspirant deserves a fair shot." },
];

export default function Mission() {
  const insets = useSafeAreaInsets();
  const share = useShare();
  return (
    <ScrollView testID="mission-screen" style={{ flex: 1, backgroundColor: colors.surface }} contentContainerStyle={{ paddingTop: insets.top + space.sm, paddingBottom: (usesNativeTabs ? insets.bottom : 0) + space.xl, paddingHorizontal: space.lg, gap: space.lg }}>
      <Animated.View entering={FadeInDown.duration(400)}>
        <LinearGradient colors={[colors.custom_series, colors.custom_darkCard]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={{ borderRadius: radius.lg, padding: space.xl, gap: space.md, overflow: "hidden" }}>
          <View pointerEvents="none" style={{ position: "absolute", top: 18, right: -38, width: 150, transform: [{ rotate: "45deg" }], backgroundColor: colors.custom_burgundy, paddingVertical: 5, alignItems: "center" }}>
            <T w="heavy" size={12} color={colors.onBrandSecondary}>100% AI</T>
          </View>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
            <Icon name="creation" size={16} color={colors.custom_whiteA70} />
            <T size={12} color={colors.custom_whiteA70}>Created by <T w="heavy" size={12} color={colors.onBrandSecondary}>AI Astra</T></T>
          </View>
          <T w="heavy" size={28} color={colors.onBrandSecondary} style={{ paddingRight: 60 }}>Built by AI.{"\n"}Made for you.</T>
          <T size={14} color={colors.custom_whiteA70}>JEELIVE.AI’s practice content and test series are designed by AI analysing every PYQ question on 80 parameters, aiming for the world’s best prediction and estimation of what to practise.</T>
          <View style={{ flexDirection: "row", gap: space.sm }}>
            {[["80", "parameters"], ["62", "daily mocks"], ["₹0", "forever"]].map(([a, b]) => (
              <View key={b} style={{ flex: 1, backgroundColor: colors.custom_whiteA15, borderRadius: radius.md, padding: space.md }}>
                <T w="heavy" size={22} color={colors.onBrandSecondary}>{a}</T>
                <T size={11} color={colors.custom_whiteA70}>{b}</T>
              </View>
            ))}
          </View>
        </LinearGradient>
      </Animated.View>

      {STEPS.map((s, i) => (
        <Animated.View key={s.title} entering={FadeInDown.delay(80 * (i + 1)).duration(380)}>
          <Card style={{ flexDirection: "row", gap: space.md }}>
            <View style={{ width: 46, height: 46, borderRadius: 14, backgroundColor: colors.custom_infoSoft, alignItems: "center", justifyContent: "center" }}>
              <Icon name={s.icon} size={26} color={colors.custom_seriesBright} />
            </View>
            <View style={{ flex: 1, gap: 2 }}>
              <T w="heavy" size={16}>{s.title}</T>
              <T size={13} color={colors.muted}>{s.body}</T>
            </View>
          </Card>
        </Animated.View>
      ))}

      <Card style={{ alignItems: "center", gap: space.md, backgroundColor: colors.brandTertiary, borderColor: colors.brandTertiary }}>
        <Image source={require("../../assets/images/jeelive-icon.png")} style={{ width: 56, height: 56, borderRadius: 14, borderWidth: 1.5, borderColor: colors.custom_neonAmber }} />
        <T w="heavy" size={20} color={colors.custom_seriesBright} style={{ textAlign: "center" }}>It’s free. Pass it on.</T>
        <T size={13} style={{ textAlign: "center" }}>Share JEELIVE.AI with your friends, batchmates and juniors. One share can change someone’s preparation.</T>
        <Button testID="mission-share-button" label="Share with friends" icon="share-variant" onPress={share} color={colors.custom_burgundy} style={{ alignSelf: "stretch" }} />
      </Card>

      <T size={11} color={colors.muted} testID="mission-disclaimer">
        “80 parameters”, “100% AI” and “world best” describe the creator’s stated AI-led design approach and ambition — not an independent audit, verified ranking or guarantee. Supplied solutions remain the original source. Score goals are practice targets, not promised results. Not affiliated with NTA.
      </T>
    </ScrollView>
  );
}
