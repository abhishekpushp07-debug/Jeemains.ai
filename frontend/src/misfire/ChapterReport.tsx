// Chapter report: every graded paper together. Which subject and which chapter cost the most marks, and whether it is
// getting better. A chapter opens its wrong questions.
import React, { useEffect, useRef } from "react";
import { StyleSheet, View } from "react-native";
import { useCached } from "@/src/useCached";
import { Empty, ErrorBox, Icon, IconName, Press, Skeleton, T } from "@/src/components/ui";
import { DCard } from "@/src/components/design";
import { TONE, Tone } from "@/src/analysis/format";
import { colors, space } from "@/src/theme";
import { ChapterReport as Report, ChapterRow, getChapters, misfireKey } from "./api";
import { chapterName, marks, slugOf } from "./parts";

const TREND: Record<string, [string, Tone, IconName]> = {
  up: ["Behtar ho raha hai", "good", "trending-up"], down: ["Kamzor ho raha hai", "bad", "trending-down"], same: ["Waisa hi", "info", "minus"],
};
function Trend({ t }: { t: ChapterRow["trend"] }) {
  const look = t ? TREND[t] : null;
  if (!look) return <T size={11} color={colors.muted}>Ek hi paper</T>;
  return <View style={styles.trend}><Icon name={look[2]} size={13} color={TONE[look[1]].ink} /><T size={11} w="bold" color={TONE[look[1]].ink}>{look[0]}</T></View>;
}

export function ChapterReport({ uid, onChapter }: { uid: string; onChapter: (subject: string, chapter: string) => void }) {
  const res = useCached<Report>(`${misfireKey(uid)}.chapters`, getChapters);
  const d = res.data, tries = useRef(0), revalidate = res.revalidate;
  // Papers finished a moment ago are still being added: ask again shortly.
  useEffect(() => {
    if (!d?.waiting || tries.current >= 8) return;
    const t = setTimeout(() => { tries.current++; revalidate(); }, 3000);
    return () => clearTimeout(t);
  }, [d, revalidate]);
  if (!d) return res.error ? <ErrorBox error={res.error} retry={res.reload} testID="chapter-report-error" /> : <View testID="chapter-report-loading" style={{ gap: space.sm }}><Skeleton h={90} /><Skeleton h={64} /><Skeleton h={64} /></View>;
  if (!d.papers) return <DCard testID="chapter-report-empty"><Empty icon="chart-box-outline" title="Abhi koi graded paper nahi hai." body="Ek mock do, report yahan banegi." /></DCard>;
  // A paper without chapter names files every question under one made-up chapter: that is not a chapter to report.
  const chapters = d.chapters.filter(c => chapterName(c.chapter));
  const most = Math.max(1, ...chapters.map(c => c.lost));
  return <View testID="chapter-report" style={{ gap: space.md }}>
    <T testID="chapter-report-papers" size={12.5} color={colors.muted}>{d.papers} paper milakar{d.waiting > 0 ? " · kuch papers abhi jud rahe hain" : ""}</T>
    <View style={styles.subjects}>
      {d.subjects.map(s => <View key={s.subject} testID={"chapter-subject-" + slugOf(s.subject)} style={styles.subject}>
        <T size={11} w="bold" color={colors.custom_eyebrow} numberOfLines={1}>{s.subject.toUpperCase()}</T>
        <T w="mono" size={20}>{s.sahi}%</T>
        <T size={11} color={colors.muted} numberOfLines={1}>sahi · {marks(s.lost)} gaye</T>
        <Trend t={s.trend} />
      </View>)}
    </View>
    {chapters.length ? chapters.map(c => <Press key={c.subject + c.chapter} testID={"chapter-row-" + slugOf(c.subject + "-" + c.chapter)} onPress={() => onChapter(c.subject, c.chapter)} scaleTo={0.99}
      accessibilityLabel={`${c.chapter}, ${c.subject}. ${marks(c.lost)} marks gaye. Iske sawaal kholo`} style={styles.row}>
      <View style={styles.rowTop}>
        <View style={{ flex: 1, minWidth: 0 }}>
          <T w="heavy" size={14} numberOfLines={2}>{c.chapter}</T>
          <T size={11.5} color={colors.muted} numberOfLines={1}>{c.subject} · {c.papers} paper · {c.total} sawaal</T>
        </View>
        <View style={{ alignItems: "flex-end" }}><T w="mono" size={15} color={colors.error}>{marks(c.lost)}</T><T size={10.5} color={colors.muted}>marks gaye</T></View>
        <View style={{ alignItems: "flex-end", minWidth: 44 }}><T w="mono" size={15}>{c.sahi}%</T><T size={10.5} color={colors.muted}>sahi</T></View>
      </View>
      <View style={styles.track}><View style={{ width: `${Math.max(4, (100 * c.lost) / most)}%`, height: "100%", borderRadius: 3, backgroundColor: TONE.bad.fill }} /></View>
      <Trend t={c.trend} />
    </Press>) : <T testID="chapter-report-no-chapters" size={12.5} color={colors.muted}>In papers mein chapter ka naam nahi likha tha, isliye sirf subject ki report hai. Chapter-wise tests do, chapter yahan dikhenge.</T>}
    {d.untagged > 0 && chapters.length > 0 ? <T testID="chapter-report-untagged" size={12} color={colors.muted}>{d.untagged} sawaal par chapter ka naam nahi tha; woh sirf subject mein gine gaye.</T> : null}
  </View>;
}

const styles = StyleSheet.create({
  trend: { flexDirection: "row", alignItems: "center", gap: 4 },
  subjects: { flexDirection: "row", gap: space.sm },
  subject: { flex: 1, minWidth: 0, gap: 2, padding: space.md, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card },
  row: { gap: 8, padding: space.md, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card },
  rowTop: { flexDirection: "row", alignItems: "center", gap: space.md },
  track: { height: 6, borderRadius: 3, backgroundColor: colors.custom_qFresh, overflow: "hidden" },
});
