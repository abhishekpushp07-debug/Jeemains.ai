import React from "react";
import { ScrollView, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInDown } from "react-native-reanimated";
import { Card, Empty, Header, Icon, IconName, Press, T } from "@/src/components/ui";
import { colors, radius, space } from "@/src/theme";
import { examBySlug } from "@/src/navigation";

export const examGrad = (slug?: string): [string, string] =>
  slug === "bitsat" ? [colors.custom_examBitsat, colors.custom_examBitsatDeep] : slug === "comedk" ? [colors.custom_darkCard, colors.custom_examComedk] : [colors.custom_examJee, colors.custom_examJeeDeep];

export default function ExamHub() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const exam = examBySlug(slug);
  const insets = useSafeAreaInsets();
  const router = useRouter();
  if (!exam) return <View style={{ flex: 1, paddingTop: insets.top }}><Empty title="Exam not found." /></View>;
  const grad = examGrad(slug);
  const items: { id: string; title: string; body: string; icon: IconName; to: string }[] = [
    { id: "mocks", title: "Mock tests", body: "Full-length exam simulations with the paper’s own rules.", icon: "file-document-multiple-outline", to: `/catalogue?slug=${slug}&kind=mocks` },
    { id: "chapters", title: "Chapter-wise practice", body: "Pick a subject and chapter. Focused, timed practice.", icon: "book-open-page-variant-outline", to: `/catalogue?slug=${slug}&kind=chapters` },
    { id: "history", title: "Results & history", body: "Every attempt for this exam, with released results.", icon: "history", to: `/catalogue?slug=${slug}&kind=history` },
  ];
  return (
    <View testID={"exam-hub-" + slug} style={{ flex: 1, backgroundColor: colors.surface }}>
      <LinearGradient colors={grad} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={{ paddingTop: insets.top + space.sm, paddingBottom: space.xl, borderBottomLeftRadius: radius.lg, borderBottomRightRadius: radius.lg }}>
        <Header title="" onBack={() => router.back()} />
        <View style={{ paddingHorizontal: space.xl, gap: 4 }}>
          <T w="bold" size={12} color={colors.custom_whiteA70} style={{ letterSpacing: 1.2 }}>EXAM HUB</T>
          <T w="heavy" size={32} color={exam.slug === "comedk" ? colors.custom_examComedkGold : colors.onBrandPrimary}>{exam.name}</T>
          <T size={14} color={colors.custom_whiteA70}>Choose how you want to practise today.</T>
        </View>
      </LinearGradient>
      <ScrollView contentContainerStyle={{ padding: space.lg, paddingBottom: insets.bottom + space.xl, gap: space.md }}>
        {items.map((it, i) => (
          <Animated.View key={it.id} entering={FadeInDown.delay(70 * i).duration(350)}>
            <Press testID={`exam-destination-${it.id}`} onPress={() => router.push(it.to as any)}>
              <Card style={{ flexDirection: "row", alignItems: "center", gap: space.md }}>
                <View style={{ width: 52, height: 52, borderRadius: 16, backgroundColor: grad[0], alignItems: "center", justifyContent: "center" }}>
                  <Icon name={it.icon} size={26} color={exam.slug === "comedk" ? colors.custom_examComedkGold : colors.onBrandPrimary} />
                </View>
                <View style={{ flex: 1 }}>
                  <T w="heavy" size={17}>{it.title}</T>
                  <T size={13} color={colors.muted}>{it.body}</T>
                </View>
                <Icon name="chevron-right" size={24} color={colors.muted} />
              </Card>
            </Press>
          </Animated.View>
        ))}
        <T size={11} color={colors.muted}>Chapter practice is focused topic work; mocks simulate the full exam. Every paper shows its own marking, timing and rules before you start.</T>
      </ScrollView>
    </View>
  );
}
