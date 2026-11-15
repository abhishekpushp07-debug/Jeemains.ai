import React, { useEffect } from "react";
import { RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { Empty, ErrorBox, IconName, Press, Skeleton, T } from "@/src/components/ui";
import { IconCircle, ScreenHeader, SectionLabel } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { colors, space } from "@/src/theme";
import { useAuth } from "@/src/auth";
import { warmExamCatalogue } from "@/src/api/catalogueWarm";
import { cachedExamName, catalogueKind, examIcon, ExamSection, sectionParam, useExam } from "@/src/api/examCatalog";
import { useListFocus } from "@/src/useListFocus";

type Item = { id: string; title: string; body: string; icon: IconName; to: string };

const LOOK: Record<string, { tint: string; wash: string }> = {
  "jee-main": { tint: colors.custom_examJee, wash: colors.custom_examJeeDeep },
  bitsat: { tint: colors.custom_examBitsat, wash: colors.custom_examBitsatDeep },
  comedk: { tint: colors.custom_examComedk, wash: colors.custom_cardRaised },
};
const sectionIcon = (s: ExamSection): IconName => (s.layout === "chapters" ? "book-open-page-variant-outline" : "file-document-multiple-outline");
const sectionBody = (s: ExamSection) => s.description?.trim() || (s.layout === "chapters" ? "Choose a subject, pick a chapter and build understanding." : "Papers published in this section on the website.");

export function ExamHub({ slug, inTab = false }: { slug: string; inTab?: boolean }) {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const { exam, sections, error, loading, refreshing, reload, revalidate } = useExam(slug);
  useListFocus(revalidate);
  useEffect(() => { if (user?.id) warmExamCatalogue(user.id, slug); }, [user?.id, slug]);
  const jee = slug === "jee-main";
  const look = LOOK[slug] ?? LOOK.comedk;
  // JEE Main keeps its PYQ papers first; every other section is the website's own list, in its order.
  const fromSite: Item[] = sections.filter(s => !(jee && s.kind === "pyq")).map(s => {
    const section = sectionParam(s);
    return { id: s.slug, title: s.name, body: sectionBody(s), icon: sectionIcon(s), to: `/catalogue?slug=${slug}&kind=${catalogueKind(s)}${section ? `&section=${encodeURIComponent(section)}` : ""}` };
  });
  // A website that sends no sections for this exam: the two boxes the app has always had.
  const defaults: Item[] = [
    { id: "mocks", title: "Mock tests", body: "Full-length exam practice with each paper’s own rules.", icon: "file-document-multiple-outline", to: `/catalogue?slug=${slug}&kind=mocks` },
    { id: "chapters", title: "Chapter-wise practice", body: "One subject. One chapter. A stronger foundation.", icon: "book-open-page-variant-outline", to: `/catalogue?slug=${slug}&kind=chapters` },
  ];
  const pyq: Item = { id: "pyq", title: "PYQ papers", body: "Original papers by year & shift. Start, continue or see your result.", icon: "file-document-check-outline", to: "/pyq" };
  // PYQ leaves with its section when the owner hides it on the website; with no section list at all it stays.
  const sent = !!exam?.sections?.length; // the website sent a section list for this exam (COMEDK sends none today)
  const pyqShown = jee && (!sent || sections.some(s => s.kind === "pyq"));
  const practice: Item[] = [...(pyqShown ? [pyq] : []), ...(sent ? fromSite : jee ? defaults.slice(1) : defaults)];
  const progress: Item = { id: "history", title: "Results & history", body: "Every attempt, saved answers and released solutions.", icon: "chart-box-outline", to: `/catalogue?slug=${slug}&kind=history` };
  const row = (item: Item, primary = false) => <Press key={item.id} testID={`exam-destination-${item.id}`} onPress={() => router.push(item.to as any)} accessibilityLabel={item.title} scaleTo={0.99} style={styles.row}>
    <IconCircle icon={item.icon} color={primary ? colors.onSurfaceInverse : colors.onSurface} bg={primary ? colors.onSurface : undefined} line={primary ? colors.onSurface : undefined} size={48} />
    <View style={styles.copy}>
      <T testID={`exam-${item.id}-title`} size={16} w="bold">{item.title}</T>
      <T testID={`exam-${item.id}-description`} size={12.5} color={colors.muted}>{item.body}</T>
    </View>
    <Glyph name="chevron-right" size={18} color={colors.custom_dim} />
  </Press>;
  const header = <ScreenHeader title={exam?.name || cachedExamName(user?.id, slug)} titleColor={colors.custom_royalMaroon} eyebrow="Exam" testID={`exam-hub-heading-${slug}`} backTestID={`exam-hub-back-${slug}`} onBack={inTab ? undefined : () => router.back()} />;
  if (!exam) return <View testID={`exam-hub-${slug}`} style={[styles.screen, { paddingTop: insets.top + space.sm }]}>
    {header}
    <View style={styles.content}>
      {loading ? <><Skeleton h={150} /><Skeleton h={170} /></> : <Empty title="This exam is not available right now." body="It may have been hidden on the website. Check Home for the current exams." />}
      <ErrorBox error={error} retry={reload} testID="exam-hub-error" />
    </View>
  </View>;
  return <View testID={`exam-hub-${slug}`} style={[styles.screen, { paddingTop: insets.top + space.sm }]}>
    {header}
    <ScrollView contentContainerStyle={[styles.content, { paddingBottom: (inTab ? 0 : insets.bottom) + space.xxl }]}
      refreshControl={<RefreshControl testID="exam-hub-refresh" refreshing={refreshing} onRefresh={reload} />}>
      <LinearGradient testID={`exam-hub-theme-${slug}`} colors={[look.wash, colors.custom_card]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
        <View style={{ flex: 1, gap: space.sm }}>
          <T w="bold" size={10.5} color={look.tint} style={{ letterSpacing: 2 }}>{jee ? "PREVIOUS YEAR PAPERS" : "FULL MOCKS · CHAPTERS"}</T>
          <T testID="exam-hub-title" size={24} w="heavy">{jee ? "real papers.\nbetter preparation." : "make your next\nattempt count."}</T>
          <T testID="exam-hub-description" size={13.5} color={colors.muted}>Choose your practice. Get straight to the questions.</T>
        </View>
        <View style={styles.mark}><Glyph name={examIcon(slug)} size={38} color={look.tint} stroke={1.3} /></View>
      </LinearGradient>
      <View style={{ gap: space.md }}>
        <SectionLabel title={jee ? "PYQ & practice" : "Practice"} />
        <View testID="exam-sections" style={styles.group}>
          {practice.map((item, i) => <View key={item.id} style={i ? styles.divider : undefined}>{row(item, i === 0)}</View>)}
          {practice.length ? null : <Empty testID="exam-sections-empty" title="No papers here yet." body="Sections appear here as soon as they are published on the website." />}
        </View>
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
