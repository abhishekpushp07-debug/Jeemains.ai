import React, { memo, useEffect, useMemo, useState } from "react";
import { FlatList, StyleSheet, TextInput, View } from "react-native";
import { Redirect, useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { api } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { useListFocus } from "@/src/useListFocus";
import { Chip, Empty, ErrorBox, Icon, Press, Skeleton, T } from "@/src/components/ui";
import { DCard, Pill, ScreenHeader, StatusLine } from "@/src/components/design";
import { GlossTabs, TabLook } from "@/src/components/GlossTabs";
import { colors, fonts, noOutline, radius, space, tabEdges } from "@/src/theme";
import { fmtClock, unixDate } from "@/src/navigation";
import { cachedExamName, catalogueAll, cataloguePath } from "@/src/api/examCatalog";
import { ClassLevel, classOf, hasClasses, useClassBook } from "@/src/classLevel";
import { useSearchTrack } from "@/src/searchTrack";

const ORDER = ["Physics", "Chemistry", "Mathematics"];
// Chapter-wise, for a subject that is split into classes: All (Class 11 first, then Class 12), or one class alone.
type ClassTab = "all" | "11" | "12";
// Glossy tabs like My Tests', each in its own colour: All baby pink, Class 11 yellow, Class 12 sky blue.
const CLASS_TABS: { key: ClassTab; label: string; look: TabLook }[] = [
  { key: "all", label: "All", look: { on: [colors.custom_tabPink, colors.custom_tabPinkDeep], rest: [colors.custom_tabPinkSoft, colors.custom_tabPinkSoftDeep], edge: tabEdges.pink, glow: colors.custom_tabPinkGlow } },
  { key: "11", label: "Class 11", look: { on: [colors.custom_tabSun, colors.custom_tabSunDeep], rest: [colors.custom_tabSunSoft, colors.custom_tabSunSoftDeep], edge: tabEdges.sun, glow: colors.custom_tabSunGlow } },
  { key: "12", label: "Class 12", look: { on: [colors.custom_tabSky, colors.custom_tabSkyDeep], rest: [colors.custom_tabSkySoft, colors.custom_tabSkySoftDeep], edge: tabEdges.sky, glow: colors.custom_tabSkyGlow } },
];
const NONE: any[] = [];
// Remember subject/search/class per exam+kind so Back never resets the list.
const remembered: Record<string, { subject: string; q: string; cls?: ClassTab }> = {};

export function attemptAction(s: any): { label: string; to: string; tone: string } {
  const a = s.attempt;
  if (a?.status === "active" || a?.resumable) return { label: "Resume", to: `/attempt/${a.id}`, tone: colors.success };
  if (a?.id && (a.status === "completed" || a.result_available)) return { label: "Result", to: `/result/${a.id}`, tone: colors.brandPrimary };
  return { label: "Start", to: `/set/${s.id}`, tone: colors.surfaceInverse };
}

const SetRow = memo(function SetRow({ s }: { s: any }) {
  const router = useRouter();
  const act = attemptAction(s);
  const available = s.live_enabled !== false && s.status === "published";
  const status = !available ? ["Unavailable", colors.custom_eyebrow] : act.label === "Resume" ? ["In progress", colors.custom_timerAmber] : act.label === "Result" ? ["Completed", colors.custom_mint] : s.saved ? ["Saved", colors.custom_savedBlue] : null;
  return (
    <Press testID={"set-row-" + s.id} disabled={!available} onPress={() => router.push(act.to as any)} scaleTo={0.985} accessibilityLabel={`${s.title}. ${available ? act.label : "Unavailable"}`}>
      <DCard style={{ flexDirection: "row", gap: space.md, alignItems: "center", padding: space.md, paddingRight: space.lg }}>
        <View style={{ width: 46, height: 46, borderRadius: 23, backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center" }}>
          <T w="heavy" size={15}>{s.chapter_number ?? s.mock_number ?? "•"}</T>
        </View>
        <View style={{ flex: 1, gap: 3 }}>
          <T testID={`set-title-${s.id}`} w="heavy" size={15} numberOfLines={2}>{s.title}</T>
          <T size={11.5} color={colors.muted}>{s.count} Q · {s.rules?.minutes ? s.rules.minutes + " min" : "Untimed"} · +{s.rules?.correct}/{s.rules?.wrong} · {s.maximum} marks</T>
          {status ? <StatusLine testID={`set-status-${s.id}`} label={status[0]} color={status[1]} /> : null}
        </View>
        {available ? (
          <View style={{ paddingHorizontal: 14, height: 36, borderRadius: radius.pill, backgroundColor: act.label === "Start" ? colors.onSurface : act.label === "Resume" ? colors.custom_timerAmber : colors.custom_cardRaised, borderWidth: act.label === "Result" ? 1 : 0, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center" }}>
            <T w="heavy" size={12} color={act.label === "Result" ? colors.onSurface : colors.custom_bar}>{act.label}</T>
          </View>
        ) : null}
      </DCard>
    </Press>
  );
});

function HistoryRow({ a }: { a: any }) {
  const router = useRouter();
  return (
    <Press testID={"history-row-" + a.id} onPress={() => router.push(((a.resumable ? "/attempt/" : "/result/") + a.id) as any)} scaleTo={0.985}>
      <DCard style={{ gap: 4 }}>
        <T w="heavy" size={10} color={colors.custom_eyebrow} style={{ letterSpacing: 1.4 }}>{unixDate(a.started_at).toUpperCase()} · {String(a.status).toUpperCase()}</T>
        <T w="heavy" size={15}>{a.title}</T>
        <T size={13} color={a.summary ? (a.summary.score < 0 ? colors.error : a.summary.score > 0 ? colors.custom_mint : colors.onSurface) : a.status === "embargoed" ? colors.muted : colors.custom_timerAmber} w="heavy">{a.summary ? `${a.summary.score} / ${a.summary.maximum}` : a.resumable ? `Resume${a.remaining_seconds ? " · " + fmtClock(Math.round(a.remaining_seconds)) + " left" : ""}` : a.status === "embargoed" ? "Result sealed until release" : "Preparing result"}</T>
      </DCard>
    </Press>
  );
}

export default function CatalogueRoute() {
  const { slug, kind, section } = useLocalSearchParams<{ slug: string; kind: string; section?: string }>();
  if (slug === "jee-main" && kind === "pyq") return <Redirect href="/pyq" />;
  return <Catalogue key={`${slug}.${kind}.${section || ""}`} />;
}

function Catalogue() {
  const { slug, kind, section = "" } = useLocalSearchParams<{ slug: string; kind: "mocks" | "chapters" | "history"; section?: string }>();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const memKey = `${user?.id}.${slug}.${kind}.${section}`;
  const [subject, setSubject] = useState(remembered[memKey]?.subject ?? (kind === "chapters" ? "Physics" : ""));
  const [q, setQ] = useState(remembered[memKey]?.q ?? "");
  const [query, setQuery] = useState(q);
  const [page, setPage] = useState(1);
  const [cls, setCls] = useState<ClassTab>(remembered[memKey]?.cls ?? "all");
  useEffect(() => { remembered[memKey] = { subject, q, cls }; }, [memKey, subject, q, cls]);
  useEffect(() => {
    const t = setTimeout(() => { if (q.trim() !== query) { setPage(1); setQuery(q.trim()); } }, 300);
    return () => clearTimeout(t);
  }, [q, query]);

  // The chapter-wise list of a subject that is split into classes (JEE Physics, Chemistry, Maths) is read whole and
  // grouped here: Class 11, then Class 12. Every other list is read a page at a time, exactly as before.
  const book = useClassBook();
  const classy = kind === "chapters" && !section && hasClasses(slug, subject);
  const path = kind === "history"
    ? `/exam-navigation/${slug}/history?page=${page}`
    : cataloguePath(slug, section ? "mocks" : kind!, section, kind === "chapters" ? subject : "", query, classy ? 1 : page);
  const valid = !!slug && (kind === "history" || kind === "mocks" || kind === "chapters");
  const fullKey = user && valid ? `u.${user.id}.${path}${classy ? "#all" : ""}` : null;
  const res = useCached<any>(fullKey, (signal) => (classy ? catalogueAll(slug, "chapters", "", subject, query, signal) : api(path, { signal })));
  useListFocus(res.revalidate);
  const items: any[] = res.data && res.dataKey === fullKey ? res.data.items : NONE;
  useSearchTrack(kind === "chapters" ? "chapters" : "papers", query, res.data && res.dataKey === fullKey ? items.length : null);
  // Each chapter's class, and the rows of the tab in view. One chapter is opened at a time, as always: a tap on a row.
  const view = useMemo(() => {
    const levels = classy ? items.map((s) => classOf(slug, subject, String(s.title || ""))) : [];
    if (!levels.some((level) => level !== null)) return { grouped: false, rows: items, n: { all: items.length, "11": 0, "12": 0 } };
    const part = (level: ClassLevel | null) => items.filter((_, i) => levels[i] === level);
    const c11 = part(11), c12 = part(12), rest = part(null);
    const under = (id: string, name: string, list: any[]) => (list.length ? [{ id, head: `${name} · ${list.length} chapter${list.length === 1 ? "" : "s"}` }, ...list] : []);
    const rows = cls === "11" ? c11 : cls === "12" ? c12 : [...under("head-11", "Class 11", c11), ...under("head-12", "Class 12", c12), ...under("head-other", "Other", rest)];
    return { grouped: true, rows, n: { all: items.length, "11": c11.length, "12": c12.length } };
  }, [classy, items, slug, subject, cls, book]); // eslint-disable-line react-hooks/exhaustive-deps
  const tabs = classy && (view.grouped || !items.length); // drawn from the start, so the list does not jump when it arrives
  const subjects = Object.keys(res.data?.subject_counts || {}).sort((a, b) => (ORDER.indexOf(a) + 99) % 99 - (ORDER.indexOf(b) + 99) % 99);
  const subjectList = subjects.length ? subjects : ORDER;
  // An exam without Physics (or a new one) opens on its own first subject.
  useEffect(() => { if (kind === "chapters" && subjects.length && !subjects.includes(subject)) { setPage(1); setSubject(subjects[0]); } }, [kind, subjects.join(), subject]); // eslint-disable-line react-hooks/exhaustive-deps
  const own = !!section; // a section the owner created on the website
  const examName = (typeof res.data?.exam === "string" && res.data.exam) || cachedExamName(user?.id, slug);
  const title = kind === "history" ? "Results & history" : res.data?.section?.name || (kind === "chapters" ? "Chapter-wise" : "Mock tests");

  return (
    <View testID={`catalogue-${slug}-${kind}`} style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <ScreenHeader title={title} eyebrow={examName} backTestID="catalogue-back-button" onBack={() => router.back()} />
      {kind !== "history" ? (
        <View style={{ paddingHorizontal: space.lg }}>
          <View style={{ flexDirection: "row", alignItems: "center", backgroundColor: colors.custom_card, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLine, paddingHorizontal: space.lg, height: 48 }}>
            <Icon name="magnify" size={20} color={colors.muted} />
            <TextInput testID="catalogue-search-input" value={q} onChangeText={setQ} placeholder={kind === "chapters" ? "Find a chapter…" : own ? "Find a paper…" : "Find a mock test…"} placeholderTextColor={colors.muted} maxLength={100} style={[{ flex: 1, fontFamily: fonts.medium, fontSize: 14, color: colors.onSurface, paddingHorizontal: space.sm }, noOutline]} />
            {q ? <Press testID="catalogue-clear-search" onPress={() => setQ("")} accessibilityLabel="Clear search" style={{ width: 44, height: 44, alignItems: "center", justifyContent: "center", marginRight: -space.md }}><Icon name="close-circle" size={18} color={colors.muted} /></Press> : null}
          </View>
        </View>
      ) : null}
      {tabs ? (
        <View testID="catalogue-class-tabs" style={styles.classTabs}>
          <GlossTabs prefix="catalogue-class" value={cls} onChange={setCls}
            items={CLASS_TABS.map((t) => ({ ...t, sub: view.grouped ? String(view.n[t.key]) : undefined, subTestID: `catalogue-class-${t.key}-count` }))} />
        </View>
      ) : null}
      {kind === "chapters" ? (
        <View style={{ height: 56, justifyContent: "center" }}>
          <FlatList horizontal showsHorizontalScrollIndicator={false} data={subjectList} keyExtractor={(x) => x}
            contentContainerStyle={{ gap: space.sm, paddingHorizontal: space.lg, alignItems: "center" }}
            renderItem={({ item }) => <Chip testID={"catalogue-subject-" + item.toLowerCase()} label={item} active={subject === item} color={colors.brandPrimary} count={res.data?.subject_counts?.[item]} onPress={() => { setPage(1); setSubject(item); }} />} />
        </View>
      ) : <View style={{ height: space.md }} />}
      <FlatList
        testID="catalogue-list"
        data={view.rows}
        initialNumToRender={8} maxToRenderPerBatch={8} windowSize={7}
        refreshing={res.refreshing} onRefresh={res.reload}
        keyExtractor={(x) => x.id}
        renderItem={({ item }) => (item.head ? <T testID={`catalogue-${item.id}`} w="heavy" size={12} color={colors.onSurface} style={styles.classHead}>{item.head.toUpperCase()}</T>
          : kind === "history" ? <HistoryRow a={item} /> : <SetRow s={item} />)}
        contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: insets.bottom + space.xl, gap: space.md }}
        ListHeaderComponent={<>
          <ErrorBox error={res.error} retry={res.reload} testID="catalogue-error" />
          {res.data ? <T w="bold" size={11} color={colors.custom_eyebrow} style={{ letterSpacing: 2, marginTop: kind === "chapters" ? space.sm : 0 }} testID="catalogue-count">{`${view.grouped && cls !== "all" ? view.rows.length : res.data.total} ${kind === "history" ? "attempts" : "live " + (kind === "chapters" ? "chapter tests" : own ? "papers" : "mock tests")}${view.grouped && cls !== "all" ? ` · Class ${cls}` : ""}`.toUpperCase()}</T> : null}
        </>}
        ListEmptyComponent={(!res.data || res.dataKey !== fullKey) && !res.error ? <View testID="catalogue-loading" style={{ gap: space.md }}><Skeleton h={76} /><Skeleton h={76} /><Skeleton h={76} /></View> : res.data ? (view.grouped ? (
          // The list has chapters, none of them in the class in view (a search can do this).
          <DCard testID="catalogue-empty-class"><Empty icon="school-outline" title={query ? `No Class ${cls} chapter matches.` : `No Class ${cls} chapter tests here yet.`}
            body={`Look in Class ${cls === "11" ? "12" : "11"}, or see every chapter.`}
            action={<Pill testID="catalogue-class-show-all" kind="outline" label="Show all chapters" onPress={() => setCls("all")} />} /></DCard>
        ) : (
          <DCard testID="catalogue-empty"><Empty icon={kind === "history" ? "history" : "file-document-outline"} title={query ? "No matching tests." : kind === "history" ? "No attempts yet." : own ? "No papers in this section yet." : kind === "mocks" ? "Full-length mocks are not live yet." : "No live tests for this subject."}
            body={query ? "Try another search." : kind === "history" ? "Your attempts for this exam will appear here." : `Reviewed ${examName} papers appear here when published. Nothing fake is shown.`}
            action={kind === "mocks" && !own ? <Pill testID="catalogue-try-chapters" kind="outline" label="Try chapter-wise practice" onPress={() => router.replace(`/catalogue?slug=${slug}&kind=chapters`)} /> : undefined} /></DCard>
        )) : undefined}
        ListFooterComponent={res.data?.pages > 1 ? (
          <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
            <Pill testID="catalogue-prev-page" kind="outline" label="Previous" icon="chevron-left" disabled={page <= 1} onPress={() => setPage((p) => p - 1)} style={{ flex: 1 }} />
            <T w="bold" size={13} testID="catalogue-page">{page} / {res.data.pages}</T>
            <Pill testID="catalogue-next-page" kind="outline" label="Next" iconRight="chevron-right" disabled={page >= res.data.pages} onPress={() => setPage((p) => p + 1)} style={{ flex: 1 }} />
          </View>) : undefined}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  classTabs: { paddingHorizontal: space.lg, marginTop: space.md },
  classHead: { letterSpacing: 1.6, marginTop: space.sm },
});
