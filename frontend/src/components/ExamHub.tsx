import React, { useEffect } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeIn, useReducedMotion } from "react-native-reanimated";
import { Empty, Icon, IconName, Press, T } from "@/src/components/ui";
import { IconCircle, ScreenHeader, SectionLabel } from "@/src/components/design";
import { ExamArt, TileKind } from "@/src/components/ExamTile";
import { colors, examGlow, space } from "@/src/theme";
import { examBySlug } from "@/src/navigation";
import { useAuth } from "@/src/auth";
import { warmExamCatalogue } from "@/src/api/catalogueWarm";

type Item = { id: string; title: string; body: string; icon: IconName; to: string };

export function ExamHub({ slug, inTab = false }: { slug: string; inTab?: boolean }) {
  const exam = examBySlug(slug);
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const reduced = useReducedMotion();
  const { user } = useAuth();
  useEffect(() => { if (user?.id) warmExamCatalogue(user.id, slug); }, [user?.id, slug]);
  if (!exam) return <View style={styles.screen}><Empty title="Exam not found." /></View>;
  const jee = slug === "jee-main";
  const kind: TileKind = jee ? "jee" : (slug as TileKind);
  const glow = examGlow(kind);
  const practice: Item[] = [
    jee ? { id: "pyq", title: "PYQ papers", body: "Original papers by year & shift. Start, continue or see your result.", icon: "file-document-check-outline", to: "/pyq" }
      : { id: "mocks", title: "Mock tests", body: "Full-length exam practice with each paper’s own rules.", icon: "file-document-multiple-outline", to: `/catalogue?slug=${slug}&kind=mocks` },
    { id: "chapters", title: "Chapter-wise practice", body: "One subject. One chapter. A stronger foundation.", icon: "book-open-page-variant-outline", to: `/catalogue?slug=${slug}&kind=chapters` },
  ];
  const progress: Item = { id: "history", title: "Results & history", body: "Every attempt, saved answers and released solutions.", icon: "chart-box-outline", to: `/catalogue?slug=${slug}&kind=history` };
  // Opacity-only entrance: rows never move under the finger, so the first tap always lands.
  const row = (item: Item, index: number, primary = false) => <Animated.View key={item.id} entering={reduced ? undefined : FadeIn.delay(index * 40).duration(220)}>
    <Press testID={`exam-destination-${item.id}`} onPress={() => router.push(item.to as any)} accessibilityLabel={item.title} scaleTo={0.985} style={[styles.row, primary && { borderColor: glow }]}>
      <IconCircle icon={item.icon} color={primary ? colors.onSurface : colors.custom_softText} bg={primary ? glow : undefined} line={primary ? glow : undefined} size={46} />
      <View style={styles.copy}>
        <T testID={`exam-${item.id}-title`} size={16} w="heavy">{item.title}</T>
        <T testID={`exam-${item.id}-description`} size={12.5} color={colors.muted}>{item.body}</T>
      </View>
      <Icon name="chevron-right" size={22} color={primary ? colors.onSurface : colors.custom_dim} />
    </Press>
  </Animated.View>;
  return <View testID={`exam-hub-${slug}`} style={[styles.screen, { paddingTop: insets.top + space.sm }]}>
    <ScreenHeader title={exam.name} eyebrow="Your exam. Your next step." testID={`exam-hub-heading-${slug}`} backTestID={`exam-hub-back-${slug}`} onBack={inTab ? undefined : () => router.back()} />
    <ScrollView contentContainerStyle={[styles.content, { paddingBottom: (inTab ? 0 : insets.bottom) + space.xxl }]}>
      <View testID={`exam-hub-theme-${slug}`} style={styles.hero}>
        <View pointerEvents="none" style={styles.clip}><View style={[styles.wash, { backgroundColor: glow }]} /></View>
        <View style={styles.heroTop}>
          <View style={{ flex: 1, gap: space.sm }}>
            <T testID="exam-hub-title" size={26} w="heavy">{jee ? "Real papers.\nBetter preparation." : "Make your\nnext attempt count."}</T>
            <T testID="exam-hub-description" size={13.5} color={colors.muted}>Choose your practice. Get straight to the questions.</T>
          </View>
          <View style={styles.art}>
            <View pointerEvents="none" style={[styles.halo, { backgroundColor: glow }]} />
            <ExamArt kind={kind} size={76} testID={`exam-hub-art-${slug}`} label={exam.name} />
          </View>
        </View>
      </View>
      <View style={{ gap: space.sm }}>
        <SectionLabel title={jee ? "PYQ & chapters" : "Mocks & chapters"} />
        {practice.map((item, i) => row(item, i, i === 0))}
      </View>
      <View style={{ gap: space.sm }}>
        <SectionLabel title="Your progress" />
        {row(progress, 2)}
      </View>
      <T testID="exam-hub-rules-note" size={11} color={colors.custom_eyebrow}>{jee ? "PYQs are previous-year full papers. Chapter practice builds individual concepts. Your attempts stay saved." : "Each paper follows its own timing and marking rules. Your progress stays saved when you leave."}</T>
    </ScrollView>
  </View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.surface },
  content: { padding: space.lg, paddingTop: space.sm, gap: space.xl },
  hero: { padding: 20, borderRadius: 24, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card },
  clip: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0, borderRadius: 24, overflow: "hidden" },
  wash: { position: "absolute", width: 220, height: 220, borderRadius: 110, top: -120, right: -80, opacity: 0.2 },
  heroTop: { flexDirection: "row", alignItems: "center", gap: space.md },
  art: { width: 92, height: 92, alignItems: "center", justifyContent: "center", transform: [{ rotate: "-6deg" }] },
  halo: { position: "absolute", width: 96, height: 96, borderRadius: 48, opacity: 0.3 },
  row: { padding: space.lg, borderRadius: 20, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card, flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 88 },
  copy: { flex: 1, gap: 3 },
});
