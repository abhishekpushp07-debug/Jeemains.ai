import React from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInDown } from "react-native-reanimated";
import { Empty, Header, Icon, IconName, Press, T } from "@/src/components/ui";
import { colors, examCardColors, radius, space } from "@/src/theme";
import { examBySlug } from "@/src/navigation";

export const examGrad = (slug?: string): [string, string] =>
  slug === "bitsat" ? [colors.custom_examBitsat, colors.custom_examBitsatDeep] : slug === "comedk" ? [colors.custom_darkCard, colors.custom_examComedk] : [colors.custom_examJee, colors.custom_examJeeDeep];

export function ExamHub({ slug, inTab = false }: { slug: string; inTab?: boolean }) {
  const exam = examBySlug(slug);
  const insets = useSafeAreaInsets();
  const router = useRouter();
  if (!exam) return <View style={styles.screen}><Empty title="Exam not found." /></View>;
  const jee = slug === "jee-main";
  const palette = examCardColors(slug === "bitsat" ? "bitsat" : slug === "comedk" ? "comedk" : "jee");
  const items: { id: string; title: string; body: string; icon: IconName; to: string }[] = [
    jee ? { id: "pyq", title: "PYQ papers", body: "Original papers by year & shift. Start, continue or see your result.", icon: "file-document-check-outline", to: "/pyq" }
      : { id: "mocks", title: "Mock tests", body: "Full-length exam practice with each paper’s own rules.", icon: "file-document-multiple-outline", to: `/catalogue?slug=${slug}&kind=mocks` },
    { id: "chapters", title: "Chapter-wise practice", body: "One subject. One chapter. A stronger foundation.", icon: "book-open-page-variant-outline", to: `/catalogue?slug=${slug}&kind=chapters` },
    { id: "history", title: "Results & history", body: "Every attempt, saved answers and released solutions.", icon: "chart-box-outline", to: `/catalogue?slug=${slug}&kind=history` },
  ];
  return <View testID={`exam-hub-${slug}`} style={[styles.screen, { paddingTop: insets.top + space.sm }]}>
    <Header title={exam.name} eyebrow="YOUR EXAM. YOUR NEXT STEP." testID={`exam-hub-heading-${slug}`} backTestID={`exam-hub-back-${slug}`} onBack={inTab ? undefined : () => router.back()} />
    <ScrollView contentContainerStyle={[styles.content, { paddingBottom: (inTab ? 0 : insets.bottom) + space.xl }]}>
      <View testID={`exam-hub-theme-${slug}`} style={[styles.intro, { backgroundColor: palette.background, borderColor: palette.line }]}>
        <View style={[styles.heroIcon, { backgroundColor: palette.iconBackground, borderColor: palette.line }]}><Icon name={jee ? "atom-variant" : slug === "bitsat" ? "flask-outline" : "school-outline"} size={40} color={palette.accent} /></View>
        <T testID="exam-hub-title" size={28} w="heavy" color={palette.ink}>{jee ? "Real papers.\nBetter preparation." : "Make your\nnext attempt count."}</T>
        <T testID="exam-hub-description" size={14} color={palette.muted}>Choose your practice. Get straight to the questions.</T>
      </View>
      {items.map((item, index) => <Animated.View key={item.id} entering={FadeInDown.delay(index * 45).duration(240)}>
        <Press testID={`exam-destination-${item.id}`} onPress={() => router.push(item.to as any)} style={[styles.card, index === 0 && styles.primaryCard]}>
          <View style={styles.icon}><Icon name={item.icon} size={26} color={colors.brandText} /></View>
          <View style={styles.copy}><T testID={`exam-${item.id}-title`} size={18} w="heavy">{item.title}</T><T testID={`exam-${item.id}-description`} size={13} color={colors.muted}>{item.body}</T></View>
          <Icon name="arrow-top-right" size={20} color={index === 0 ? colors.brandText : colors.muted} />
        </Press>
      </Animated.View>)}
      <T testID="exam-hub-rules-note" size={11} color={colors.mutedSecondary}>{jee ? "PYQs are previous-year full papers. Chapter practice builds individual concepts. Your attempts stay saved." : "Each paper follows its own timing and marking rules. Your progress stays saved when you leave."}</T>
    </ScrollView>
  </View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.surface },
  content: { padding: space.lg, gap: space.lg },
  intro: { gap: space.sm, padding: 20, borderRadius: 18, borderWidth: 1, overflow: "hidden" },
  heroIcon: { width: 70, height: 70, borderRadius: 22, backgroundColor: colors.brandTertiary, borderWidth: 1, borderColor: colors.brandLine, justifyContent: "center", alignItems: "center", marginBottom: space.sm },
  card: { padding: space.lg, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surfaceSecondary, flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 100 },
  primaryCard: { borderColor: colors.brandLine },
  icon: { width: 44, height: 48, alignItems: "center", justifyContent: "center" },
  copy: { flex: 1, gap: 4 },
});