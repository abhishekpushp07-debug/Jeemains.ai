import React, { useEffect } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { Empty, IconName, Press, T } from "@/src/components/ui";
import { IconCircle, ScreenHeader, SectionLabel } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { colors, space } from "@/src/theme";
import { examBySlug } from "@/src/navigation";
import { useAuth } from "@/src/auth";
import { warmExamCatalogue } from "@/src/api/catalogueWarm";

type Item = { id: string; title: string; body: string; icon: IconName; to: string };

const LOOK: Record<string, { icon: IconName; tint: string; wash: string }> = {
  "jee-main": { icon: "atom-variant", tint: colors.custom_examJee, wash: colors.custom_examJeeDeep },
  bitsat: { icon: "school-outline", tint: colors.custom_examBitsat, wash: colors.custom_examBitsatDeep },
  comedk: { icon: "office-building-outline", tint: colors.custom_examComedk, wash: colors.custom_cardRaised },
};

export function ExamHub({ slug, inTab = false }: { slug: string; inTab?: boolean }) {
  const exam = examBySlug(slug);
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  useEffect(() => { if (user?.id) warmExamCatalogue(user.id, slug); }, [user?.id, slug]);
  if (!exam) return <View style={styles.screen}><Empty title="Exam not found." /></View>;
  const jee = slug === "jee-main";
  const look = LOOK[slug] ?? LOOK.comedk;
  const practice: Item[] = [
    jee ? { id: "pyq", title: "PYQ papers", body: "Original papers by year & shift. Start, continue or see your result.", icon: "file-document-check-outline", to: "/pyq" }
      : { id: "mocks", title: "Mock tests", body: "Full-length exam practice with each paper’s own rules.", icon: "file-document-multiple-outline", to: `/catalogue?slug=${slug}&kind=mocks` },
    { id: "chapters", title: "Chapter-wise practice", body: "One subject. One chapter. A stronger foundation.", icon: "book-open-page-variant-outline", to: `/catalogue?slug=${slug}&kind=chapters` },
  ];
  const progress: Item = { id: "history", title: "Results & history", body: "Every attempt, saved answers and released solutions.", icon: "chart-box-outline", to: `/catalogue?slug=${slug}&kind=history` };
  const row = (item: Item, primary = false) => <Press key={item.id} testID={`exam-destination-${item.id}`} onPress={() => router.push(item.to as any)} accessibilityLabel={item.title} scaleTo={0.99} style={styles.row}>
    <IconCircle icon={item.icon} color={primary ? colors.onSurfaceInverse : colors.onSurface} bg={primary ? colors.onSurface : undefined} line={primary ? colors.onSurface : undefined} size={48} />
    <View style={styles.copy}>
      <T testID={`exam-${item.id}-title`} size={16} w="bold">{item.title}</T>
      <T testID={`exam-${item.id}-description`} size={12.5} color={colors.muted}>{item.body}</T>
    </View>
    <Glyph name="chevron-right" size={18} color={colors.custom_dim} />
  </Press>;
  return <View testID={`exam-hub-${slug}`} style={[styles.screen, { paddingTop: insets.top + space.sm }]}>
    <ScreenHeader title={exam.name} titleColor={colors.custom_royalMaroon} eyebrow="Exam" testID={`exam-hub-heading-${slug}`} backTestID={`exam-hub-back-${slug}`} onBack={inTab ? undefined : () => router.back()} />
    <ScrollView contentContainerStyle={[styles.content, { paddingBottom: (inTab ? 0 : insets.bottom) + space.xxl }]}>
      <LinearGradient testID={`exam-hub-theme-${slug}`} colors={[look.wash, colors.custom_card]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
        <View style={{ flex: 1, gap: space.sm }}>
          <T w="bold" size={10.5} color={look.tint} style={{ letterSpacing: 2 }}>{jee ? "PREVIOUS YEAR PAPERS" : "FULL MOCKS · CHAPTERS"}</T>
          <T testID="exam-hub-title" size={24} w="heavy">{jee ? "real papers.\nbetter preparation." : "make your next\nattempt count."}</T>
          <T testID="exam-hub-description" size={13.5} color={colors.muted}>Choose your practice. Get straight to the questions.</T>
        </View>
        <View style={styles.mark}><Glyph name={look.icon} size={38} color={look.tint} stroke={1.3} /></View>
      </LinearGradient>
      <View style={{ gap: space.md }}>
        <SectionLabel title={jee ? "PYQ & chapters" : "Mocks & chapters"} />
        <View style={styles.group}>{practice.map((item, i) => <View key={item.id} style={i ? styles.divider : undefined}>{row(item, i === 0)}</View>)}</View>
      </View>
      <View style={{ gap: space.md }}>
        <SectionLabel title="Your progress" />
        <View style={styles.group}>{row(progress)}</View>
      </View>
      <T testID="exam-hub-rules-note" size={11.5} color={colors.custom_eyebrow}>{jee ? "PYQs are previous-year full papers. Chapter practice builds individual concepts. Your attempts stay saved." : "Each paper follows its own timing and marking rules. Your progress stays saved when you leave."}</T>
    </ScrollView>
  </View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.surface },
  content: { padding: space.lg, paddingTop: space.sm, gap: space.xl },
  hero: { padding: 22, borderRadius: 24, borderWidth: 1, borderColor: colors.custom_cardLine, flexDirection: "row", alignItems: "center", gap: space.md },
  mark: { width: 76, height: 76, borderRadius: 38, backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLine, alignItems: "center", justifyContent: "center" },
  group: { borderRadius: 22, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card, overflow: "hidden" },
  divider: { borderTopWidth: 1, borderTopColor: colors.custom_barLine },
  row: { paddingHorizontal: space.lg, paddingVertical: space.lg, flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 84 },
  copy: { flex: 1, gap: 3 },
});
