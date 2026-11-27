// "Sab": the website's Misfire as it is. Every open question of every paper (newest paper first), the ones already
// understood, and the chapter report. Filters by subject and chapter.
import React, { useEffect, useRef, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Empty, ErrorBox, Icon, Press, Skeleton, T } from "@/src/components/ui";
import { DCard, DSheet, Pill } from "@/src/components/design";
import { colors, space } from "@/src/theme";
import { MisfireItem, MisfirePage, MisfireSummary, getPage, misfireKey } from "./api";
import { ChapterReport } from "./ChapterReport";
import { PillRow, QuestionRow, chapterName } from "./parts";
import { applied, openQueue, usePatches } from "./store";
import { usePaged } from "./usePaged";

type Mode = "open" | "fixed" | "chapters";

export function AllTab({ uid, summary, startSubject = "", startChapter = "" }: { uid: string; summary: MisfireSummary | null; startSubject?: string; startChapter?: string }) {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  usePatches();
  const [mode, setMode] = useState<Mode>("open");
  const [subject, setSubject] = useState(startSubject);
  const [chapter, setChapter] = useState(startChapter);
  const [sheet, setSheet] = useState(false);
  const status = mode === "fixed" ? "fixed" : "open";
  const list = usePaged<MisfireItem, MisfirePage>(mode === "chapters" ? null : `${misfireKey(uid)}.list.${status}.${subject}.${chapter}`, (page, signal) => getPage(status, subject, chapter, page, signal));
  const rows = list.items.map(applied).filter(i => i.status === status);
  const waiting = list.first?.waiting || 0, tries = useRef(0), revalidate = list.revalidate;
  // Papers finished a moment ago are still being added to Misfire: ask again shortly.
  useEffect(() => {
    if (!waiting || tries.current >= 8) return;
    const t = setTimeout(() => { tries.current++; revalidate(); }, 3000);
    return () => clearTimeout(t);
  }, [waiting, list.first, revalidate]);
  const chapters = (list.first?.chapters || []).filter(c => chapterName(c.name));
  const subjects = (summary?.subjects || []).filter(s => s[status] > 0);
  const open = (index: number) => { openQueue(rows, index); router.push("/misfire/solve" as any); };

  const head = <View style={{ gap: space.md, paddingBottom: space.sm }}>
    <PillRow prefix="misfire-mode" value={mode} onChange={k => { setMode(k as Mode); setChapter(""); }}
      items={[{ key: "open", label: "Galtiyan", count: summary?.open }, { key: "fixed", label: "Samajh gaya", count: summary?.fixed }, { key: "chapters", label: "Chapter report" }]} />
    {mode !== "chapters" ? <>
      {subjects.length ? <PillRow prefix="misfire-subject" value={subject} onChange={k => { setSubject(k); setChapter(""); }}
        items={[{ key: "", label: "Sab" }, ...subjects.map(s => ({ key: s.name, label: s.name, count: s[status] }))]} /> : null}
      {mode === "open" && (summary?.open || 0) > 0 ? <Press testID="misfire-mock-cta" onPress={() => router.push("/misfire/mock/new" as any)} scaleTo={0.99}
        accessibilityLabel="Inhi galtiyon se mock banao" style={styles.mock}>
        <Icon name="fire" size={18} color={colors.custom_chipBlood} />
        <View style={{ flex: 1, minWidth: 0 }}>
          <T w="heavy" size={14} color={colors.custom_chipBloodDeep}>Inhi galtiyon se mock banao</T>
          <T size={11.5} color={colors.custom_softText} numberOfLines={1}>Subject, chapter aur ginti chuno · JEE Main jaisa</T>
        </View>
        <Icon name="arrow-right" size={18} color={colors.custom_chipBlood} />
      </Press> : null}
      {chapters.length > 1 || chapter ? <Press testID="misfire-chapter-filter" onPress={() => setSheet(true)} accessibilityLabel={`Chapter: ${chapter || "saare"}. Badlo`} style={styles.chapter}>
        <Icon name="filter-variant" size={16} color={colors.custom_softText} />
        <T w="bold" size={13} numberOfLines={1} style={{ flex: 1 }}>{chapter || "Saare chapter"}</T>
        {chapter ? <Press testID="misfire-chapter-clear" onPress={() => setChapter("")} accessibilityLabel="Chapter filter hatao" hitSlop={8}><Icon name="close-circle" size={18} color={colors.custom_eyebrow} /></Press>
          : <Icon name="chevron-down" size={18} color={colors.custom_eyebrow} />}
      </Press> : null}
      {waiting > 0 ? <T testID="misfire-waiting" size={12.5} color={colors.muted}>Aapke kuch papers abhi jud rahe hain…</T> : null}
      <ErrorBox error={list.error && !list.first ? list.error : ""} retry={list.reload} testID="misfire-error" />
    </> : null}
  </View>;

  return <>
    <FlatList testID="misfire-list" data={mode === "chapters" ? [] : rows} keyExtractor={i => i.id} initialNumToRender={10} windowSize={7}
      contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: insets.bottom + space.xxl, gap: space.sm }}
      refreshControl={<RefreshControl refreshing={false} onRefresh={list.reload} />}
      ListHeaderComponent={head}
      renderItem={({ item, index }) => <View style={{ gap: space.sm }}>
        {/* Questions of one paper sit together under its name. */}
        {index === 0 || rows[index - 1].attempt_id !== item.attempt_id ? <T testID={`misfire-paper-head-${index}`} w="heavy" size={11} color={colors.custom_eyebrow} numberOfLines={1} style={styles.paper}>{item.title.toUpperCase()}</T> : null}
        <QuestionRow testID={`misfire-row-${index}`} item={item} onPress={() => open(index)} />
      </View>}
      ListEmptyComponent={mode === "chapters" ? undefined : list.loading && !list.first ? <View testID="misfire-loading" style={{ gap: space.sm }}><Skeleton h={58} /><Skeleton h={58} /><Skeleton h={58} /></View>
        : list.first ? <DCard testID="misfire-empty"><Empty icon={mode === "open" ? "check-circle-outline" : "bookmark-outline"}
          title={mode === "open" ? "Koi galti baaki nahi." : "Abhi tak koi sawaal “Samajh gaya” nahi hua."}
          body={mode === "open" ? "Agla mock do; jo galat ya chhoot jaye, yahan aa jayega." : "Galtiyan mein sawaal dobara solve karo; sahi hote hi “Samajh gaya” dabao."} /></DCard> : undefined}
      ListFooterComponent={mode === "chapters" ? <ChapterReport uid={uid} onChapter={(s, c) => { setSubject(s); setChapter(c); setMode("open"); }} />
        : <View style={{ gap: space.sm, paddingTop: space.sm }}>
          <ErrorBox error={list.moreError} testID="misfire-more-error" />
          {list.hasMore ? <Pill testID="misfire-more" kind="outline" label="Aur dikhao" busy={list.busy} onPress={list.more} /> : null}
        </View>} />
    <DSheet visible={sheet} onClose={() => setSheet(false)} testID="misfire-chapter-sheet" title="Chapter chuno">
      {[{ name: "", count: list.first?.total ?? 0 }, ...chapters].map((c, i) => <Press key={c.name || "all"} testID={`misfire-chapter-${i}`} onPress={() => { setChapter(c.name); setSheet(false); }}
        accessibilityState={{ selected: chapter === c.name }} style={[styles.pick, chapter === c.name && styles.pickOn]}>
        <T w={chapter === c.name ? "heavy" : "medium"} size={14} style={{ flex: 1 }}>{c.name || "Saare chapter"}</T>
        {c.name ? <T w="bold" size={12} color={colors.muted}>{c.count}</T> : null}
      </Press>)}
    </DSheet>
  </>;
}

const styles = StyleSheet.create({
  chapter: { minHeight: 46, flexDirection: "row", alignItems: "center", gap: 8, paddingHorizontal: space.md, borderRadius: 14, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card },
  mock: { minHeight: 56, flexDirection: "row", alignItems: "center", gap: 10, paddingHorizontal: space.md, paddingVertical: 8, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_chipBlood, backgroundColor: colors.custom_chipBloodSoft },
  paper: { letterSpacing: 1.4, marginTop: space.sm },
  pick: { minHeight: 48, flexDirection: "row", alignItems: "center", gap: space.sm, paddingHorizontal: space.md, borderRadius: 12, borderWidth: 1, borderColor: colors.custom_cardLine },
  pickOn: { borderColor: colors.onSurface, backgroundColor: colors.custom_cardRaised },
});
